import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QComboBox, QLabel, QLineEdit, QMessageBox,
                             QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.colors import red

# 风险等级配置
risk_map = {
    "V": "5",
    "IV": "4",
    "III": "3",
    "II": "2",
    "I": "1"
}
risk_list = ["V", "IV", "III", "II", "I"]

# 内置中文字体
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_CN = 'STSong-Light'

# 默认坐标参数（风险等级标注）
DEFAULT_X = 30
DEFAULT_Y = 813
X_MIN, X_MAX = 10, 200
Y_MIN, Y_MAX = 700, 850


class PDFRiskAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("电力通信工作票PDF风险等级标注工具")
        self.setFixedSize(580, 480)
        self.pdf_path = ""

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)

        # 1. 文件选择区
        self.btn_select = QPushButton("选择PDF文件")
        self.btn_select.clicked.connect(self.select_pdf)
        layout.addWidget(self.btn_select)

        self.label_file = QLabel("未选择文件")
        self.label_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_file)

        # 2. 风险等级下拉
        layout.addWidget(QLabel("作业风险等级："))
        self.combo_risk = QComboBox()
        self.combo_risk.addItems(risk_list)
        self.combo_risk.setCurrentText("V")
        layout.addWidget(self.combo_risk)

        # 3. 单选框组：是否填写红色“无”
        layout.addWidget(QLabel("是否自动填写【现场补充安全措施】红色“无”："))
        radio_group_layout = QHBoxLayout()
        self.radio_group = QButtonGroup()
        self.radio_enable = QRadioButton("启用（彩色打印推荐）")
        self.radio_disable = QRadioButton("关闭（黑白打印建议勾选此项）")
        self.radio_disable.setChecked(True)
        self.radio_group.addButton(self.radio_enable, 1)
        self.radio_group.addButton(self.radio_disable, 0)
        radio_group_layout.addWidget(self.radio_enable)
        radio_group_layout.addWidget(self.radio_disable)
        layout.addLayout(radio_group_layout)

        # 4. 坐标参数设置区域
        layout.addWidget(QLabel("==== 风险等级文字位置参数 ===="))
        row_x = QHBoxLayout()
        row_x.addWidget(QLabel(f"左右偏移X({X_MIN}~{X_MAX})："))
        self.edit_x = QLineEdit(str(DEFAULT_X))
        self.edit_x.setToolTip("数值变大，文字向右移动；变小向左")
        row_x.addWidget(self.edit_x)
        layout.addLayout(row_x)

        row_y = QHBoxLayout()
        row_y.addWidget(QLabel(f"上下偏移Y({Y_MIN}~{Y_MAX})："))
        self.edit_y = QLineEdit(str(DEFAULT_Y))
        self.edit_y.setToolTip("数值变大，文字向上移动；变小向下")
        row_y.addWidget(self.edit_y)
        layout.addLayout(row_y)

        self.btn_reset_pos = QPushButton("重置风险标注默认坐标")
        self.btn_reset_pos.clicked.connect(self.reset_position)
        layout.addWidget(self.btn_reset_pos)

        # 5. 生成PDF按钮
        self.btn_run = QPushButton("生成最终标注PDF文件")
        self.btn_run.clicked.connect(self.annotate_pdf)
        layout.addWidget(self.btn_run)

        layout.addStretch()

        # 底部版权&仓库栏
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(4)
        label_ver = QLabel("软件版本：20260701-v2.5")
        label_ver.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_ver.setStyleSheet("font-size:10px; color:#555555;")
        footer_layout.addWidget(label_ver)

        label_repo_tip = QLabel("开源仓库（更新下载、问题反馈）：")
        label_repo_tip.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_repo_tip.setStyleSheet("font-size:9px; color:#555555;")
        footer_layout.addWidget(label_repo_tip)

        label_repo_url = QLabel("https://github.com/bh3bbb/power-workticket-risk-annotator")
        label_repo_url.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_repo_url.setStyleSheet("font-size:9px; color:#0066cc;")
        footer_layout.addWidget(label_repo_url)

        label_copyright = QLabel("Open Source under MIT License | Copyright (c) 2026 Guangyuan Ding(BH3BBB)")
        label_copyright.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_copyright.setStyleSheet("font-size:9px; color:#555555;")
        footer_layout.addWidget(label_copyright)
        layout.addLayout(footer_layout)

    def reset_position(self):
        self.edit_x.setText(str(DEFAULT_X))
        self.edit_y.setText(str(DEFAULT_Y))

    def get_position_value(self):
        try:
            x = int(self.edit_x.text())
            y = int(self.edit_y.text())
        except ValueError:
            QMessageBox.warning(self, "参数错误", "偏移值必须输入整数！")
            return None
        if not (X_MIN <= x <= X_MAX):
            QMessageBox.warning(self, "参数超出范围", f"左右X必须在 {X_MIN} ~ {X_MAX} 之间")
            return None
        if not (Y_MIN <= y <= Y_MAX):
            QMessageBox.warning(self, "参数超出范围", f"上下Y必须在 {Y_MIN} ~ {Y_MAX} 之间")
            return None
        return (x, y)

    def select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择PDF", "", "PDF 文件 (*.pdf)"
        )
        if path:
            self.pdf_path = path
            self.label_file.setText(os.path.basename(path))

    def find_safety_page(self, pdf_reader):
        """兼容低版本PyPDF2，仅检索哪一页包含目标文字"""
        target_text = "7.现场补充安全措施："
        for page_num, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            if target_text in text:
                return page_num
        return None

    def annotate_pdf(self):
        try:
            if not self.pdf_path:
                self.label_file.setText("请先选择PDF文件！")
                return
            pos = self.get_position_value()
            if pos is None:
                return
            draw_x, draw_y = pos
            selected_roman = self.combo_risk.currentText()
            risk_text = f"作业风险等级：{selected_roman}级"

            reader = PdfReader(self.pdf_path)
            writer = PdfWriter()
            enable_fill_safety = self.radio_group.checkedId() == 1
            target_page_idx = None
            if enable_fill_safety:
                target_page_idx = self.find_safety_page(reader)

            temp_water = "tmp_mark_layer.pdf"
            for page_idx, page in enumerate(reader.pages):
                c = canvas.Canvas(temp_water, pagesize=A4)
                c.setFont(FONT_CN, 14)
                # 首页绘制风险等级黑色文字
                if page_idx == 0:
                    c.setFillColor("black")
                    c.drawString(draw_x, draw_y, risk_text)
                # 匹配页面绘制红色“无”，固定左对齐，适配你工作票排版
                if enable_fill_safety and target_page_idx is not None and page_idx == target_page_idx:
                    c.setFillColor(red)
                    c.setFont(FONT_CN, 15)
                    # 固定左偏移40，垂直位置适配标准工作票横线
                    c.drawString(40, 130, "无")
                c.save()
                mark_reader = PdfReader(temp_water)
                page.merge_page(mark_reader.pages[0])
                writer.add_page(page)
            # 清理临时文件
            if os.path.exists(temp_water):
                os.remove(temp_water)

            # 输出文件
            dir_name, file_name = os.path.split(self.pdf_path)
            name_no_ext, ext = os.path.splitext(file_name)
            out_name = f"{name_no_ext}_标注完成{ext}"
            out_path = os.path.join(dir_name, out_name)
            with open(out_path, "wb") as f:
                writer.write(f)

            tip_msg = f"完成！输出：{out_name}\n风险等级已添加至首页"
            if enable_fill_safety and target_page_idx is not None:
                tip_msg += f"，已在第{target_page_idx+1}页填写红色「无」"
            elif enable_fill_safety and target_page_idx is None:
                tip_msg += "，未检测到【7.现场补充安全措施】文字，跳过红字填写"
            self.label_file.setText(tip_msg)
        except Exception as e:
            QMessageBox.critical(self, "处理失败", f"PDF处理异常：{str(e)}")
            if os.path.exists("tmp_mark_layer.pdf"):
                os.remove("tmp_mark_layer.pdf")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PDFRiskAnnotator()
    win.show()
    sys.exit(app.exec())
