from PIL import Image, ImageOps
import streamlit as st
import numpy as np
import pandas as pd
import out_pdf

st.title("表千家茶道部 道具カタログ 作成")

csv_file = st.file_uploader("カタログ csv のアップロード", type='csv')
img_dir = st.file_uploader("画像フォルダのアップロード", accept_multiple_files='directory')

if csv_file != None:
    df = pd.read_csv(csv_file, comment="#")

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
if img_dir:
    img_path_list = [img.name for img in img_dir]
    img_file_names = [img_path.split("/")[-1] for img_path in img_path_list]
    
    df_show_img = pd.DataFrame({
        "img": img_dir,
        "path": img_path_list,
        "name": img_file_names
    })
    
    for row in df_selected.itertuples():
        file_name = row[-1]
        if file_name in df_show_img['name'].to_list():
            img = df_show_img[df_show_img['name']==file_name]['img'].iloc[0]
            img = Image.open(img)
            img = ImageOps.exif_transpose(img)
            col_img, col_text = st.columns([1, 2])
            with col_text:
                st.write(f"道具名: {row[1]}")
                st.write(f"作者: {row[4]}")
                st.write(f"作品名: {row[3]}")
            with col_img:
                st.image(img, use_container_width=True)
    img_dict = {
        img.name.split("/")[-1]: img
        for img in img_dir
    }

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
