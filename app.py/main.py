import streamlit as st

# タイトル
st.title("🤖 AI Teacher アプリ")

# 説明文
st.write("質問の入力や、画像のアップロードができます。")

# テキスト入力欄
user_input = st.text_input("質問をどうぞ：", placeholder="例：この画像について教えてください")

# 画像アップロード機能（ここを追加しました！）
uploaded_file = st.file_uploader("画像をアップロード（PNG, JPG, JPEG）", type=["png", "jpg", "jpeg"])

# アップロードされた画像があれば画面に表示する
if uploaded_file is not None:
    st.image(uploaded_file, caption="アップロードされた画像", use_column_width=True)

# ボタンと処理
if st.button("送信する"):
    if user_input or uploaded_file:
        st.success("受け付けました！")
        if user_input:
            st.write(f"**質問内容:** {user_input}")
        if uploaded_file:
            st.write("**画像:** 正常に読み込まれました")
    else:
        st.warning("質問を入力するか、画像をアップロードしてください。")
