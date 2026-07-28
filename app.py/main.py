import streamlit as st
from google import genai
from PIL import Image

# ページ設定
st.title("🤖 AI Teacher アプリ")
st.write("画像や質問を入力すると、AIの先生が分かりやすく解説します！")

# StreamlitのSecretsからAPIキーを取得してクライアントを初期化
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("APIキーの設定を確認してください。SecretsにGEMINI_API_KEYが登録されているか確認しましょう。")
    st.stop()

# ユーザー入力エリア
user_input = st.text_input("質問をどうぞ：", placeholder="例：（１）を教えてください")
uploaded_file = st.file_uploader("画像をアップロード（PNG, JPG, JPEG）", type=["png", "jpg", "jpeg"])

image = None
if uploaded_file is not None:
    # 画像を開いて表示
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

# 送信ボタンを押したときの処理
if st.button("送信する"):
    if not user_input and not uploaded_file:
        st.warning("質問を入力するか、画像をアップロードしてください。")
    else:
        with st.spinner("AI先生が考え中..."):
            try:
                # 先生としてのシステムプロンプト（指示書き）
                system_instruction = (
                    "あなたは親切で分かりやすい学校の先生です。"
                    "小中学生にも伝わるように丁寧な言葉遣いで、ステップを踏んで解説してください。"
                )

                # 送信するコンテンツの準備
                contents = []
                if image:
                    contents.append(image)
                if user_input:
                    contents.append(user_input)
                else:
                    contents.append("この画像について詳しく解説してください。")

                # Gemini 2.5 Flash モデルで回答を生成
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=contents,
                    config={"system_instruction": system_instruction}
                )

                # 回答の表示
                st.success("AI先生からの回答：")
                st.write(response.text)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
