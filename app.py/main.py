import base64
import io
import os
import openai
from PIL import Image
import streamlit as st

# --------------------------------------------------
# ページ基本設定
# --------------------------------------------------
st.set_page_config(
    page_title="チャット先生！ - 個別指導アシスタント",
    page_icon="👩‍🏫",
    layout="centered",
)

# --------------------------------------------------
# サイドバー（設定・カスタマイズエリア）
# --------------------------------------------------
st.sidebar.title("⚙️ 画面表示・設定")

st.sidebar.subheader("1. ヘッダー情報の変更")
custom_caption = st.sidebar.text_input(
    "サブタイトル（キャッチフレーズ）",
    value="－個別指導アシスタント－"
)
custom_title = st.sidebar.text_input(
    "メインタイトル",
    value="チャット先生！"
)

st.sidebar.subheader("2. 先生の画像設定")
image_option = st.sidebar.radio(
    "画像の読み込み方法",
    ["標準（teacher.jpgまたはサンプル）", "画像URLを指定", "PCから画像をアップロード"]
)

teacher_img = None

if image_option == "標準（teacher.jpgまたはサンプル）":
    if os.path.exists("teacher.jpg"):
        teacher_img = "teacher.jpg"
    else:
        teacher_img = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9d1-200d-1f3eb.png"

elif image_option == "画像URLを指定":
    url_input = st.sidebar.text_input(
        "画像のURLを入力",
        value="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9d1-200d-1f3eb.png"
    )
    teacher_img = url_input if url_input else None

elif image_option == "PCから画像をアップロード":
    sidebar_file = st.sidebar.file_uploader("先生の画像をアップロード", type=["png", "jpg", "jpeg"])
    if sidebar_file is not None:
        teacher_img = Image.open(sidebar_file)

st.sidebar.subheader("3. 案内メッセージの変更")
custom_info = st.sidebar.text_area(
    "メッセージ文章",
    value=(
        "チャット先生です！\n\n"
        "私は間違えた問題、分からない問題、解き方が自信がない問題等について、"
        "チャットをしながら解決し、弱点克服を目指します。\n\n"
        "「今、分からない！」に即、対応、あなたの学習をサポートします。"
    ),
    height=150
)

# --------------------------------------------------
# 1. ヘッダーエリア（サイドバーの設定を反映）
# --------------------------------------------------
st.caption(custom_caption)
st.title(custom_title)

col1, col2 = st.columns([1, 1])

with col1:
    if teacher_img is not None:
        st.image(teacher_img, use_column_width=True)
    else:
        st.warning("画像が設定されていません")

with col2:
    st.info(custom_info)

st.markdown("---")

# --------------------------------------------------
# 2. 学習の仕方ガイド
# --------------------------------------------------
st.subheader("🔷 学習の仕方")
st.write(
    "1. 下の **「画像をアップロード」** に問題の写真を貼り付けます（任意）。\n"
    "2. **「質問・問題番号入力」** に「(3)が分かりません」などと入力します。\n"
    "3. **「送信する」** ボタンを押すと、チャット先生が解説します！"
)

st.markdown("---")

# --------------------------------------------------
# 3. APIキー設定の確認
# --------------------------------------------------
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("APIキーの設定を確認してください。SecretsにOPENAI_API_KEYが登録されているか確認しましょう。")
    st.stop()

client = openai.OpenAI(api_key=api_key)

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# --------------------------------------------------
# 4. ユーザー入力・アップロードエリア
# --------------------------------------------------
uploaded_file = st.file_uploader(
    "📷 問題を貼り付け（画像をアップロード）", type=["png", "jpg", "jpeg"]
)

image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="貼り付けされた問題画像", use_column_width=True)

user_input = st.text_input(
    "✍️ 質問・問題番号を入力",
    placeholder="例：(3)の解説をお願いします！",
)

# --------------------------------------------------
# 5. 送信・AI回答エリア
# --------------------------------------------------
if st.button("送信する", type="primary"):
    if not user_input and not uploaded_file:
        st.warning("質問を入力するか、問題を貼り付けてください。")
    else:
        with st.spinner("チャット先生が考え中..."):
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

                system_prompt = """
                あなたは丁寧で親しみやすい個別指導の先生「チャット先生」です。
                生徒が「今、分からない！」と思っている問題や問題番号に対して、分かりやすく親切に答えてください。
                解き方のヒントやステップを丁寧に教え、最後は励ましの言葉で締めくくってください。
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    max_tokens=1000,
                )

                st.markdown("### 👩‍🏫 チャット先生からの回答")
                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
