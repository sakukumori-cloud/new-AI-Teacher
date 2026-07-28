import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# ページ設定
st.title("🤖 AI Teacher アプリ")
st.write("画像や質問を入力すると、AIの先生が分かりやすく解説します！")

# APIキーの設定
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("APIキーの設定を確認してください。SecretsにGEMINI_API_KEYが登録されているか確認しましょう。")
    st.stop()

# クライアントの作成
client = genai.Client(api_key=api_key)

# ユーザー入力エリア
user_input = st.text_input("質問をどうぞ：", placeholder="例：(3) を教えてください")
uploaded_file = st.file_uploader("画像をアップロード（PNG, JPG, JPEG）", type=["png", "jpg", "jpeg"])

image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

# 送信ボタンを押したときの処理
if st.button("送信する"):
    if not user_input and not uploaded_file:
        st.warning("質問を入力するか、画像をアップロードしてください。")
    else:
        with st.spinner("AI先生が考え中..."):
            try:
                # 1. コンテンツ（テキスト・画像）の準備
                contents = []

                if user_input:
                    contents.append(user_input)

                if image is not None:
                    contents.append(image)

                # 2. システム指示（システムプロンプト）の設定
                config = types.GenerateContentConfig(
                    system_instruction="あなたは親切で分かりやすい学校の先生です。"
                )

                # 3. モデル呼び出し（標準・安定の gemini-2.0-flash）
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=contents,
                    config=config
                )

                # 4. 画面に表示
                st.write(response.text)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
