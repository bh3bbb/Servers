import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QFileDialog, QComboBox, QLabel)
from PyQt6.QtCore import Qt
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
# 新增：使用reportlab内置开源中文字体
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# 风险等级配置：从大到小排序，默认V
risk_map = {
    "V": "5",
    "IV": "4",
    "III": "3",
    "II": "2",
    "I": "1"
}
risk_list = ["V", "IV", "III", "II", "I"]

# 注册内置中文字体（STSong-Light 宋体，原生支持中文，无需外部ttf）
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_CN = 'STSong-Light'


class PDFRiskAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("电力通信工作票PDF风险等级标注工具 x64")
        self.setFixedSize(480, 220)
        self.pdf_path = ""

        # 界面布局
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)

        # 1. 文件选择按钮
        self.btn_select = QPushButton("选择PDF文件")
        self.btn_select.clicked.connect(self.select_pdf)
        layout.addWidget(self.btn_select)

        # 2. 文件路径显示
        self.label_file = QLabel("未选择文件")
        self.label_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_file)

        # 3. 风险等级下拉框
        self.combo_risk = QComboBox()
        self.combo_risk.addItems(risk_list)
        self.combo_risk.setCurrentText("V")  # 默认V级
        layout.addWidget(QLabel("作业风险等级："))
        layout.addWidget(self.combo_risk)

        # 4. 执行标注按钮
        self.btn_run = QPushButton("生成带风险等级的PDF")
        self.btn_run.clicked.connect(self.annotate_pdf)
        layout.addWidget(self.btn_run)

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

        selected_roman = self.combo_risk.currentText()
        level_num = risk_map[selected_roman]
        text_content = f"作业风险等级：{selected_roman}级"

        # 临时水印PDF（存放左上角文字）
        temp_water = "tmp_watermark.pdf"
        c = canvas.Canvas(temp_water, pagesize=A4)
        # 设置中文字体、字号
        c.setFont(FONT_CN, 14)
        # 左上角坐标：x=30, y=800（A4纸左上角基准）
        c.drawString(30, 800, text_content)
        c.save()

        # 读取原PDF + 水印PDF合并
        reader = PdfReader(self.pdf_path)
        water_reader = PdfReader(temp_water)
        writer = PdfWriter()

        for page in reader.pages:
            page.merge_page(water_reader.pages[0])
            writer.add_page(page)

        # 输出新文件
        dir_name, file_name = os.path.split(self.pdf_path)
        name_no_ext, ext = os.path.splitext(file_name)
        out_name = f"{name_no_ext}_风险标注{ext}"
        out_path = os.path.join(dir_name, out_name)

        with open(out_path, "wb") as f:
            writer.write(f)

        # 删除临时文件
        os.remove(temp_water)
        self.label_file.setText(f"完成！输出：{out_name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PDFRiskAnnotator()
    win.show()
    sys.exit(app.exec())
