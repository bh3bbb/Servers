import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QComboBox, QLabel, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

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

# 默认坐标参数（已修改Y默认值813）
DEFAULT_X = 30
DEFAULT_Y = 813
# 参数限制范围
X_MIN, X_MAX = 10, 200
Y_MIN, Y_MAX = 700, 850


class PDFRiskAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        # 修改2：程序主标题
        self.setWindowTitle("电力通信工作票PDF风险等级标注工具")
        self.setFixedSize(520, 380)
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

        # 3. 坐标参数设置区域
        layout.addWidget(QLabel("==== 标注位置参数设置 ===="))
        # X偏移行
        row_x = QHBoxLayout()
        row_x.addWidget(QLabel(f"左右偏移X({X_MIN}~{X_MAX})："))
        self.edit_x = QLineEdit(str(DEFAULT_X))
        self.edit_x.setToolTip("数值变大，文字向右移动；变小向左")
        row_x.addWidget(self.edit_x)
        layout.addLayout(row_x)

        # Y偏移行
        row_y = QHBoxLayout()
        row_y.addWidget(QLabel(f"上下偏移Y({Y_MIN}~{Y_MAX})："))
        self.edit_y = QLineEdit(str(DEFAULT_Y))
        self.edit_y.setToolTip("数值变大，文字向上移动；变小向下")
        row_y.addWidget(self.edit_y)
        layout.addLayout(row_y)

        # 重置默认坐标按钮
        self.btn_reset_pos = QPushButton("重置为默认坐标")
        self.btn_reset_pos.clicked.connect(self.reset_position)
        layout.addWidget(self.btn_reset_pos)

        # 4. 生成PDF按钮
        self.btn_run = QPushButton("生成带风险等级的PDF")
        self.btn_run.clicked.connect(self.annotate_pdf)
        layout.addWidget(self.btn_run)

        # 填充空白占位
        layout.addStretch()

        # 修改3：右下角版本+版权信息
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(4)
        # 版本号
        label_ver = QLabel("软件版本：20260701-v2.2")
        label_ver.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_ver.setStyleSheet("font-size:10px; color:#555555;")
        footer_layout.addWidget(label_ver)
        # 版权信息
        label_copyright = QLabel("Copyright(c) [2026] [Guangyuan Ding(BH3BBB)]. All rights reserved.")
        label_copyright.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_copyright.setStyleSheet("font-size:9px; color:#555555;")
        footer_layout.addWidget(label_copyright)
        layout.addLayout(footer_layout)

    def reset_position(self):
        """一键恢复默认坐标"""
        self.edit_x.setText(str(DEFAULT_X))
        self.edit_y.setText(str(DEFAULT_Y))

    def get_position_value(self):
        """校验输入框数字合法性"""
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

    def annotate_pdf(self):
        if not self.pdf_path:
            self.label_file.setText("请先选择PDF文件！")
            return

        pos = self.get_position_value()
        if pos is None:
            return
        draw_x, draw_y = pos

        selected_roman = self.combo_risk.currentText()
        text_content = f"作业风险等级：{selected_roman}级"

        temp_water = "tmp_watermark.pdf"
        c = canvas.Canvas(temp_water, pagesize=A4)
        c.setFont(FONT_CN, 14)
        # 使用界面自定义坐标绘制文字
        c.drawString(draw_x, draw_y, text_content)
        c.save()

        reader = PdfReader(self.pdf_path)
        water_reader = PdfReader(temp_water)
        writer = PdfWriter()

        # ========== 关键修改：仅首页添加标注，其余页面原样输出 ==========
        for idx, page in enumerate(reader.pages):
            if idx == 0:
                # 第一页合并水印文字
                page.merge_page(water_reader.pages[0])
            writer.add_page(page)

        dir_name, file_name = os.path.split(self.pdf_path)
        name_no_ext, ext = os.path.splitext(file_name)
        out_name = f"{name_no_ext}_风险标注{ext}"
        out_path = os.path.join(dir_name, out_name)

        with open(out_path, "wb") as f:
            writer.write(f)

        os.remove(temp_water)
        self.label_file.setText(f"完成！输出：{out_name}（仅首页添加风险等级标注）")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PDFRiskAnnotator()
    win.show()
    sys.exit(app.exec())
