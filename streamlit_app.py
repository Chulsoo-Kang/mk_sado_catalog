from PIL import Image, ImageOps
from pathlib import Path
from io import BytesIO
import streamlit as st
import numpy as np
import pandas as pd
import out_pdf, csv



def read_catalog_csv(csv_file):
    text = csv_file.getvalue().decode("utf-8-sig").splitlines()
    reader = csv.reader(text)

    header = next(reader)
    base_cols = header[:6]  # 道具名, 種類, 作品名, 作者, 個数, 備考

    rows = []
    for line in reader:
        base = line[:6]
        image_names = line[6:]

        # 空欄を除去
        image_names = [x.strip() for x in image_names if x.strip()]

        row = dict(zip(base_cols, base))
        row["画像ファイル名"] = image_names
        rows.append(row)

    return pd.DataFrame(rows)


def stem_name(filename):
    return Path(filename).stem.lower()


def make_img_dict(uploaded_imgs):
    return {
        stem_name(img.name.split("/")[-1]): img.getvalue()
        for img in uploaded_imgs
    }


st.title("表千家茶道部 道具カタログ 作成")

csv_file = st.file_uploader("カタログ csv のアップロード", type='csv')
img_dir = st.file_uploader(
    "画像フォルダのアップロード",
    accept_multiple_files="directory"
)

img_files = st.file_uploader(
    "画像ファイルを複数アップロード",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if csv_file != None:
    df = read_catalog_csv(csv_file)

    selected_item = st.sidebar.multiselect(
        "道具を選択",
        options = df['道具名'].unique(),
        default = df['道具名'].unique()
    )

    selected_artists = st.sidebar.multiselect(
        "作者を選択",
        options = df['作者'].unique(),
        default = df['作者'].unique()
    )

    df_selected = df[df['道具名'].isin(selected_item) & df['作者'].isin(selected_artists)]
    st.write(df_selected)

    img_dict = {}
    uploaded_imgs = []

    if img_dir:
        uploaded_imgs.extend(img_dir)

    if img_files:
        uploaded_imgs.extend(img_files)

    if uploaded_imgs:
        img_path_list = [img.name for img in uploaded_imgs]
        img_file_names = [img_path.split("/")[-1] for img_path in img_path_list]

        df_show_img = pd.DataFrame({
            "img": uploaded_imgs,
            "path": img_path_list,
            "name": img_file_names
        })

        img_dict = make_img_dict(uploaded_imgs)

        for _, row in df_selected.iterrows():
            image_names = row["画像ファイル名"]

            st.subheader(f"{row['道具名']}：{row['作品名']}")

            col_text, col_img = st.columns([2, 3])

            with col_text:
                st.write(f"道具名: {row['道具名']}")
                st.write(f"種類: {row['種類']}")
                st.write(f"作者: {row['作者']}")
                st.write(f"個数: {row['個数']}")
                st.write(f"備考: {row['備考']}")

            with col_img:
                for image_name in image_names:
                    key = stem_name(image_name)

                    if key in img_dict:
                        img_bytes = img_dict[key]

                        img = Image.open(BytesIO(img_bytes))
                        img = ImageOps.exif_transpose(img)

                        st.image(img, use_container_width=True)

    if st.sidebar.button("現在表示中のカタログをPDF化"):
        progress = st.sidebar.progress(0)
        status_text = st.sidebar.empty()

        status_text.write("PDF作成を開始しています...")
        progress.progress(10)

        status_text.write("画像とカタログ情報を処理中...")
        progress.progress(40)

        pdf_path = out_pdf.make_catalog_pdf(df_selected, img_dict)

        status_text.write("PDFファイルを準備中...")
        progress.progress(80)

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        progress.progress(100)
        status_text.success("PDF作成が完了しました。")

        st.sidebar.download_button(
            label="PDFをダウンロード",
            data=pdf_bytes,
            file_name="sadou_catalog.pdf",
            mime="application/pdf"
        )
