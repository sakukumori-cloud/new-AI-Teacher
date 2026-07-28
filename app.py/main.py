import base64
import io
import openai
from PIL import Image
import streamlit as st

# ページ設定
st.set_page_config(page_title="AI Teacher アプリ", page_icon="🤖")
st.title("🤖 AI Teacher アプリ")

# --------------------------------------------------
# 1. 先生のプロンプト（フェイス内容）設定
# --------------------------------------------------
SYSTEM_PROMPT = """
あなたは明るく親しみやすい学校の先生「チャット先生」です。
以下のルールを守って回答してください：
- 丁寧で分かりやすい言葉遣い（親しみやすい敬語）を使う
- 難しい専門用語は身近な例えを使って説明する
- 最後に生徒を励ますような前向きな一言を添える
"""

# --------------------------------------------------
# 2. APIキーのチェック
# --------------------------------------------------
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
  st.error(
      "APIキーの設定を確認してください。SecretsにOPENAI_API_KEYが登録されているか確認しましょう。"
  )
  st.stop()

client = openai.OpenAI(api_key=api_key)


# 画像をbase64エンコードする関数
def encode_image(image):
  buffered = io.BytesIO()
  image.save(buffered, format="JPEG")
  return base64.b64encode(buffered.getvalue()).decode("utf-8")


# --------------------------------------------------
# 3. 画面レイアウト（先生の画像や挨拶）
# --------------------------------------------------
# 先生の画像（Web上の画像URLまたはGitHub内の画像ファイルパスを指定）
# ※ご自身の好きな画像URLに変更可能です
TEACHER_IMAGE_URL = (
    "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9d1-200d-1f3eb.png"
)

col1, col2 = st.columns([1, 4])
with col1:
  st.image(TEACHER_IMAGE_URL, width=100)
with col2:
  st.write("こんにちは！チャット先生だよ。何でも質問してね！")

st.divider()

# --------------------------------------------------
# 4. ユーザー入力エリア
# --------------------------------------------------
user_input = st.text_input(
    "質問をどうぞ：", placeholder="例：(3) を教えてください"
)
uploaded_file = st.file_uploader(
    "画像をアップロード（PNG, JPG, JPEG）", type=["png", "jpg", "jpeg"]
)

image = None
if uploaded_file is not None:
  image = Image.open(uploaded_file)
  st.image(image, caption="アップロードされた画像", use_column_width=True)

# --------------------------------------------------
# 5. 送信処理
# --------------------------------------------------
if st.button("送信する"):
  if not user_input and not uploaded_file:
    st.warning("質問を入力するか、画像をアップロードしてください。")
  else:
    with st.spinner("AI先生が考え中..."):
      try:
        user_content = []

        if user_input:
          user_content.append({"type": "text", "text": user_input})

        if image is not None:
          base64_image = encode_image(image.convert("RGB"))
          user_content.append({
              "type": "image_url",
              "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
          })

        # API呼び出し
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=1000,
        )

        st.markdown("### 👨‍🏫 チャット先生からの回答")
        st.write(response.choices[0].message.content)

      except Exception as e:
        st.error(f"エラーが発生しました: {e}")
