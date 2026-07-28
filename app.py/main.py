import base64
import io
import openai
from PIL import Image
import streamlit as st

# ページ設定
st.set_page_config(page_title="AI Teacher アプリ", page_icon="🤖")

# --------------------------------------------------
# 1. サイドバー（管理・カスタマイズ画面）
# --------------------------------------------------
st.sidebar.header("⚙️ 先生のカスタマイズ")

# ① キャッチコピー・挨拶の変更
custom_greeting = st.sidebar.text_input(
    "あいさつ・キャッチ",
    value="こんにちは！チャット先生だよ。何でも質問してね！",
)

# ② 画像の指定（URLまたはファイルアップロード）
image_option = st.sidebar.radio(
    "先生の画像の指定方法", ["URLで指定", "画像をアップロード"]
)

teacher_img = None
if image_option == "URLで指定":
  default_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9d1-200d-1f3eb.png"
  img_url = st.sidebar.text_input("画像URL", value=default_url)
  teacher_img = img_url
else:
  uploaded_teacher_img = st.sidebar.file_uploader(
      "先生の画像をアップロード", type=["png", "jpg", "jpeg"]
  )
  if uploaded_teacher_img:
    teacher_img = Image.open(uploaded_teacher_img)

# ③ システムプロンプト（性格・ルール）の編集
system_prompt = st.sidebar.text_area(
    "先生の性格・ルール（プロンプト）",
    value="""あなたは明るく親しみやすい学校の先生「チャット先生」です。
以下のルールを守って回答してください：
- 丁寧で分かりやすい言葉遣い（親しみやすい敬語）を使う
- 難しい専門用語は身近な例えを使って説明する
- 最後に生徒を励ますような前向きな一言を添える""",
    height=150,
)

# --------------------------------------------------
# 2. メイン画面表示（カスタマイズ結果を即座に反映）
# --------------------------------------------------
st.title("🤖 AI Teacher アプリ")

col1, col2 = st.columns([1, 4])
with col1:
  if teacher_img:
    st.image(teacher_img, width=100)
  else:
    st.write("🤖")  # 画像がない場合の予備表示
with col2:
  # サイドバーで入力したキャッチコピーを表示
  st.write(f"### {custom_greeting}")

st.divider()

# --------------------------------------------------
# 3. APIキーのチェック
# --------------------------------------------------
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
  st.error(
      "APIキーの設定を確認してください。SecretsにOPENAI_API_KEYが登録されているか確認しましょう。"
  )
  st.stop()

client = openai.OpenAI(api_key=api_key)


def encode_image(image):
  buffered = io.BytesIO()
  image.save(buffered, format="JPEG")
  return base64.b64encode(buffered.getvalue()).decode("utf-8")


# --------------------------------------------------
# 4. ユーザー質問入力エリア
# --------------------------------------------------
user_input = st.text_input(
    "質問をどうぞ：", placeholder="例：(3) を教えてください"
)
uploaded_file = st.file_uploader(
    "質問の画像をアップロード（PNG, JPG, JPEG）",
    type=["png", "jpg", "jpeg"],
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

        # API呼び出し（サイドバーで編集したプロンプトを適用）
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=1000,
        )

        st.markdown("### 👨‍🏫 チャット先生からの回答")
        st.write(response.choices[0].message.content)

      except Exception as e:
        st.error(f"エラーが発生しました: {e}")
