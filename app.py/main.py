import streamlit as st
import openai
from PIL import Image
import base64
import io

# ページ設定
st.title("🤖 AI Teacher アプリ")
st.write("画像や質問を入力すると、AIの先生が分かりやすく解説します！")

# APIキーの設定
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("APIキーの設定を確認してください。SecretsにOPENAI_API_KEYが登録されているか確認しましょう。")
    st.stop()

# Clientの作成
client = openai.OpenAI(api_key=api_key)

# 画像をbase64エンコードする関数
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

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
                # ユーザーメッセージの作成
                user_content = []

                if user_input:
                    user_content.append({"type": "text", "text": user_input})

                if image is not None:
                    # 画像をJPEG形式でエンコードして追加
                    base64_image = encode_image(image.convert("RGB"))
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })

                # API呼び出し
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "あなたは親切で分かりやすい学校の先生です。"
                        },
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ],
                    max_tokens=1000
                )

                # 画面に表示
                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
