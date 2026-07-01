import sys
import os
import fitz  # PyMuPDF PDF预览
from io import BytesIO
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QComboBox, QLabel, QLineEdit, QMessageBox,
                             QScrollArea)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QFont

# 风险等级配置
risk_map = {
    "V": "5",
    "IV": "4",
    "III": "3",
    "II": "2",
    "I": "1"
}
risk_list = ["V", "IV", "III", "II", "I"]

# ReportLab内置中文字体
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_CN = 'STSong-Light'

# 默认坐标与范围
DEFAULT_X = 30
DEFAULT_Y = 820
X_MIN, X_MAX = 10, 200
Y_MIN, Y_MAX = 700, 850
FONT_SIZE = 14

# A4标准尺寸 pt
A4_W = 595
A4_H = 842

class PDFRiskAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("电力通信工作票PDF风险等级标注工具 x64（带预览）")
        self.resize(960, 680)
        self.pdf_path = ""
        self.doc = None  # fitz文档对象
        self.page_pix = None
        self.scale = 0.75

        # 主布局：左右分栏
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ========== 左侧控制面板 ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_panel.setFixedWidth(420)

        # 1. 文件选择
        self.btn_select = QPushButton("选择PDF文件")
        self.btn_select.clicked.connect(self.select_pdf)
        left_layout.addWidget(self.btn_select)
        self.label_file = QLabel("未选择文件")
        self.label_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.label_file)

        # 2. 风险等级
        left_layout.addWidget(QLabel("作业风险等级："))
        self.combo_risk = QComboBox()
        self.combo_risk.addItems(risk_list)
        self.combo_risk.setCurrentText("V")
        self.combo_risk.currentTextChanged.connect(self.refresh_preview)
        left_layout.addWidget(self.combo_risk)

        # 3. 位置参数
        left_layout.addWidget(QLabel("==== 标注位置参数设置 ===="))
        # X偏移
        row_x = QHBoxLayout()
        row_x.addWidget(QLabel(f"左右偏移X({X_MIN}~{X_MAX})："))
        self.edit_x = QLineEdit(str(DEFAULT_X))
        self.edit_x.textChanged.connect(self.refresh_preview)
        self.edit_x.setToolTip("数值变大文字向右，变小向左")
        row_x.addWidget(self.edit_x)
        left_layout.addLayout(row_x)
        # Y偏移
        row_y = QHBoxLayout()
        row_y.addWidget(QLabel(f"上下偏移Y({Y_MIN}~{Y_MAX})："))
        self.edit_y = QLineEdit(str(DEFAULT_Y))
        self.edit_y.textChanged.connect(self.refresh_preview)
        self.edit_y.setToolTip("数值变大文字向上，变小向下")
        row_y.addWidget(self.edit_y)
        left_layout.addLayout(row_y)

        # 重置按钮
        self.btn_reset_pos = QPushButton("重置为默认坐标")
        self.btn_reset_pos.clicked.connect(self.reset_position)
        left_layout.addWidget(self.btn_reset_pos)

        # 生成PDF按钮
        self.btn_run = QPushButton("生成带风险等级的PDF")
        self.btn_run.clicked.connect(self.annotate_pdf)
        left_layout.addWidget(self.btn_run)

        # 填充空白
        left_layout.addStretch()

        # ========== 右侧预览面板 ==========
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        self.preview_label = QLabel("请先选择PDF文件，此处为实时预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border:1px solid #aaa; background:#f8f8f8;")
        right_scroll.setWidget(self.preview_label)

        # 加入主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_scroll)

    def reset_position(self):
        self.edit_x.setText(str(DEFAULT_X))
        self.edit_y.setText(str(DEFAULT_Y))

    def get_pos_int(self):
        try:
            x = int(self.edit_x.text())
            y = int(self.edit_y.text())
        except ValueError:
            return None
        if not (X_MIN <= x <= X_MAX and Y_MIN <= y <= Y_MAX):
            return None
        return (x, y)

    def select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF (*.pdf)")
        if not path:
            return
        self.pdf_path = path
        self.label_file.setText(os.path.basename(path))
        # 加载PDF预览
        if self.doc:
            self.doc.close()
        self.doc = fitz.open(path)
        self.refresh_preview()

    def refresh_preview(self):
        """实时刷新预览，绘制蓝色标注文字提示框"""
        if not self.doc:
            self.preview_label.setText("请先选择PDF文件")
            self.preview_label.setPixmap(QPixmap())
            return
        pos = self.get_pos_int()
        page = self.doc[0]
        # 渲染PDF页面
        mat = fitz.Matrix(self.scale, self.scale)
        pix = page.get_pixmap(matrix=mat)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                     QImage.Format_RGB888 if not pix.alpha else QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(img)

        # 在预览图上绘制标注文字框
        painter = QPainter(pixmap)
        painter.setPen(QColor(0, 80, 255))
        painter.setFont(QFont("SimSun", 12))
        text = f"作业风险等级：{self.combo_risk.currentText()}级"
        if pos:
            x_pt, y_pt = pos
            # PDF坐标系左下角为原点，Qt预览左上角为原点，转换Y
            draw_x = x_pt * self.scale
            draw_y = (A4_H - y_pt) * self.scale
            painter.drawText(int(draw_x), int(draw_y), text)
            # 绘制文字外框方便定位
            rect = painter.boundingRect(int(draw_x), int(draw_y)-16, 320, 30, Qt.TextFlag.TextSingleLine, text)
            painter.drawRect(rect)
        painter.end()
        self.preview_label.setPixmap(pixmap)

    def annotate_pdf(self):
        if not self.pdf_path:
            self.label_file.setText("请先选择PDF文件！")
            return
        pos = self.get_pos_int()
        if pos is None:
            QMessageBox.warning(self, "参数错误", "坐标数值非法或超出范围！")
            return
        draw_x, draw_y = pos
        text_content = f"作业风险等级：{self.combo_risk.currentText()}级"

        # 生成临时水印PDF
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont(FONT_CN, FONT_SIZE)
        c.drawString(draw_x, draw_y, text_content)
        c.save()
        buf.seek(0)

        # 合并PDF
        from PyPDF2 import PdfReader, PdfWriter
        reader = PdfReader(self.pdf_path)
        overlay_reader = PdfReader(buf)
        writer = PdfWriter()
        for page in reader.pages:
            page.merge_page(overlay_reader.pages[0])
            writer.add_page(page)

        # 输出文件
        dir_name, file_name = os.path.split(self.pdf_path)
        name_no_ext, ext = os.path.splitext(file_name)
        out_name = f"{name_no_ext}_风险标注{ext}"
        out_path = os.path.join(dir_name, out_name)
        with open(out_path, "wb") as f:
            writer.write(f)
        self.label_file.setText(f"完成！输出：{out_name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PDFRiskAnnotator()
    win.show()
    sys.exit(app.exec())
