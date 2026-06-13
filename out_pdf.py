from tempfile import NamedTemporaryFile
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageOps

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def stem_name(filename):
    return Path(str(filename)).stem.lower()


def make_rl_image(img_bytes, max_width, max_height):
    img = Image.open(BytesIO(img_bytes))
    img = ImageOps.exif_transpose(img)

    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG")
    buf.seek(0)

    w, h = img.size
    scale = min(max_width / w, max_height / h)

    return RLImage(buf, width=w * scale, height=h * scale)


def make_catalog_pdf(df_selected, img_dict):
    tmp_pdf = NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = tmp_pdf.name
    tmp_pdf.close()

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    styles["Title"].fontName = "HeiseiKakuGo-W5"
    styles["Normal"].fontName = "HeiseiKakuGo-W5"

    story = []

    story.append(Paragraph("表千家茶道部 道具カタログ", styles["Title"]))
    story.append(Spacer(1, 20))

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

    item_count = 0

    for _, row in df_selected.iterrows():
        item_story = []

        title = str(row["作品名"]) if str(row["作品名"]) != "nan" else str(row["道具名"])
        item_story.append(Paragraph(f"作品名：{title}", styles["Title"]))
        item_story.append(Spacer(1, 6))

        info_text = f"""
        道具名：{row['道具名']}<br/>
        種類：{row['種類']}<br/>
        作者：{row['作者']}<br/>
        個数：{row['個数']}<br/>
        備考：{row['備考']}
        """
        item_story.append(Paragraph(info_text, styles["Normal"]))
        item_story.append(Spacer(1, 8))

        valid_images = []

        for filename in row["画像ファイル名"]:
            key = stem_name(filename)
            if key in img_dict:
                valid_images.append(img_dict[key])

        n_img = len(valid_images)

        if n_img > 0:
            usable_width = 480
            max_width = usable_width / n_img - 8

            if n_img == 1:
                max_height = 260
            else:
                max_height = 180

            image_cells = [
                make_rl_image(img_bytes, max_width, max_height)
                for img_bytes in valid_images
            ]

            image_table = Table([image_cells])
            image_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))

            item_story.append(image_table)

        item_box = Table([[item_story]], colWidths=[500])
        item_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))

        story.append(item_box)
        story.append(Spacer(1, 12))

        item_count += 1

        if item_count % 2 == 0:
            story.append(PageBreak())

    doc.build(story)

    return pdf_path
