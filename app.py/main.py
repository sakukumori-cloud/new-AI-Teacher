import streamlit as st
import google.generativeai as genai
from PIL import Image

# ページ設定
st.title("🤖 AI Teacher アプリ")
st.write("画像や質問を入力すると、AIの先生が分かりやすく解説します！")

# APIキーの設定
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("APIキーの設定を確認してください。SecretsにGEMINI_API_KEYが登録されているか確認しましょう。")
    st.stop()

genai.configure(api_key=api_key)

# ユーザー入力エリア
user_input = st.text_input("質問をどうぞ：", placeholder="例：（３）を教えてください")
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
                # 軽量・高速な1.5-flash-8bモデルを使用
                model = genai.GenerativeModel("gemini-1.5-flash-8b")

                # 送信するプロンプトの準備
                prompt_parts = []
                system_prompt = (
                    "あなたは親切で分かりやすい学校の先生です。"
                    "小中学生にも伝わるように丁寧な言葉遣いで、ステップを踏んで解説してください。\n\n"
                )
                
                if user_input:
                    prompt_parts.append(system_prompt + f"質問：{user_input}")
                else:
                    prompt_parts.append(system_prompt + "この画像の問題について詳しく解説してください。")

                if image:
                    prompt_parts.append(image)

                # 回答の生成
                response = model.generate_content(prompt_parts)

                # 回答の表示
                st.success("AI先生からの回答：")
                st.write(response.text)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
