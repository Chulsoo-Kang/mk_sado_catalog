from tempfile import NamedTemporaryFile
from PIL import Image, ImageOps
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,Table, TableStyle, PageBreak)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def make_catalog_pdf(df_selected, img_dict):
    tmp_pdf = NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = tmp_pdf.name
    tmp_pdf.close()

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()

    styles["Title"].fontName = "HeiseiKakuGo-W5"
    styles["Normal"].fontName = "HeiseiKakuGo-W5"

    story = []

    story.append(Paragraph("表千家茶道部 道具カタログ", styles["Title"]))
    story.append(Spacer(1, 20))

    # カタログ表
    table_cols = ["道具名", "種類", "作品名", "作者", "個数", "備考", "画像ファイル名"]
    data = [table_cols]

    for _, row in df_selected.iterrows():
        data.append([str(row[col]) for col in table_cols])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))

    story.append(table)
    story.append(PageBreak())

    # 各道具の詳細
    for _, row in df_selected.iterrows():
        story.append(Paragraph(f"道具名：{row['道具名']}", styles["Title"]))
        story.append(Spacer(1, 10))

        story.append(Paragraph(f"種類：{row['種類']}", styles["Normal"]))
        story.append(Paragraph(f"作品名：{row['作品名']}", styles["Normal"]))
        story.append(Paragraph(f"作者：{row['作者']}", styles["Normal"]))
        story.append(Paragraph(f"個数：{row['個数']}", styles["Normal"]))
        story.append(Paragraph(f"備考：{row['備考']}", styles["Normal"]))
        story.append(Spacer(1, 10))

        filename = str(row["画像ファイル名"])

        if filename in img_dict:
            img_file = img_dict[filename]

            img = Image.open(img_file)
            img = ImageOps.exif_transpose(img)

            tmp_img = NamedTemporaryFile(delete=False, suffix=".jpg")
            img.convert("RGB").save(tmp_img.name)

            story.append(RLImage(tmp_img.name, width=220, height=220))

        story.append(PageBreak())

    doc.build(story)

    return pdf_path