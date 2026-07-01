# power-workticket-risk-annotator
README.md
Power Workticket Risk Annotator / 电力工作票风险标注工具
Windows x64 GUI Tool | MIT Open Source
软件版本：20260701-v2.1

---
📌 项目简介 / Introduction
中文：
本工具为电力通信工作票专用 PDF 风险等级标注工具，基于 Python & PyQt6 开发。支持自定义作业风险等级（罗马数字 I–V，默认 V 级），可自由调整标注坐标，仅在 PDF 第一页添加风险等级文字，后续页面保持原样，适用于电力班组日常工作票归档使用。
English：
A lightweight Windows GUI tool designed for power communication work ticket processing. It adds operation risk level marks on the first page only of PDF files. Supports adjustable position parameters and Roman numeral risk levels (I–V). Suitable for daily power industry document archiving.

---
✨ 核心功能 / Features
中文功能：
- 支持风险等级选择：V、IV、III、II、I（从高到低排序，默认 V 级）
- 可自定义 左右 X / 上下 Y 标注偏移坐标，带数值范围限制
- 仅对 PDF 首页添加风险标注，第二页及后续页面无修改
- 内置中文字体，PDF 中文渲染正常无乱码、无空白
- 一键重置默认坐标、一键导出新 PDF（不覆盖原文件）
- 纯本地离线运行，无网络上传、无数据泄露
English Features：
- Risk level selection: V, IV, III, II, I (descending order, default: V)
- Fully adjustable X/Y offset for text position customization
- Annotate only the first page, keep other pages untouched
- Built-in Chinese font, no garbled characters in exported PDF
- One-click reset and export, original file will not be overwritten
- 100% offline local processing, no data upload

---
🖥 使用方式 / Usage
中文：
1. 运行 PDF风险标注工具.exe
2. 选择需要处理的工作票 PDF 文件
3. 选择对应作业风险等级
4. 微调 X/Y 坐标避免文字重叠，或直接使用默认参数
5. 点击生成，自动输出带标注的新 PDF 文件
English：
1. Run PDF风险标注工具.exe
2. Select your work ticket PDF file
3. Choose the correct operation risk level
4. Adjust X/Y offset if needed, or use default values
5. Generate new annotated PDF file automatically

---
⚙ 参数说明 / Parameters
默认参数 Default：
- X（左右偏移）：30（范围 10–200）
- Y（上下偏移）：813（范围 700–850）
- Default Risk Level: V (Level 5)

---
📄 开源协议 / License
中文：
本项目基于 MIT License 开源，可自由使用、修改、分发，个人与企业内部均可免费使用。
English：
This project is open sourced under the MIT License. Free for personal and enterprise internal use, modification and distribution.
Copyright (c) 2026 Guangyuan Ding (BH3BBB)

---
🌐 仓库地址 / Repository
https://github.com/bh3bbb/power-workticket-risk-annotator
