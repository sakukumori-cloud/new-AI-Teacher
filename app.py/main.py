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

# 会話履歴の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# サイドバー（設定・カスタマイズエリア）
# --------------------------------------------------
st.sidebar.title("⚙️ 画面表示・設定")

if st.sidebar.button("💬 会話履歴をリセット", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

st.sidebar.subheader("1. ヘッダー情報の変更")
custom_caption = st.sidebar.text_input("サブタイトル", value="－個別指導アシスタント－")
custom_title = st.sidebar.text_input("メインタイトル", value="チャット先生！")

st.sidebar.subheader("2. 先生の画像設定")
image_option = st.sidebar.radio(
    "画像の読み込み方法",
    ["標準（teacher.jpgまたはサンプル）", "画像URLを指定", "PCから画像をアップロード"]
)

teacher_img = None
if image_option == "標準（teacher.jpgまたはサンプル）":
    if os.path.exists("app.py/teacher.jpg"):
        teacher_img = "app.py/teacher.jpg"
    elif os.path.exists("teacher.jpg"):
        teacher_img = "teacher.jpg"
    else:
        teacher_img = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9d1-200d-1f3eb.png"
elif image_option == "画像URLを指定":
    url_input = st.sidebar.text_input("画像のURLを入力", value="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9d1-200d-1f3eb.png")
    teacher_img = url_input if url_input else None
elif image_option == "PCから画像をアップロード":
    sidebar_file = st.sidebar.file_uploader("先生の画像をアップロード", type=["png", "jpg", "jpeg"])
    if sidebar_file is not None:
        teacher_img = Image.open(sidebar_file)

st.sidebar.subheader("3. 案内メッセージの変更")
custom_info = st.sidebar.text_area(
    "メッセージ文章",
    value="挽回先生です！\n\n間違えた問題や解き方に自信がない問題について、一緒にやり取りしながら解決を目指します。",
    height=150
)

st.sidebar.markdown("---")
st.sidebar.subheader("🧪 AI先生の指示（プロンプト調整）")

default_system_prompt = """あなたは個別指導のベテランの「挽回先生」です。生徒が送ってきた画像と質問をもとに、対話しながら一緒に解いていきます。

【最重要：問題番号の特定手順】
1. 生徒が「2(1)」「問2(1)」「２（１）」など『番号のみ』を入力してきた場合、画像の中からまず大きな数字の「2」または「大問2」「問2」があるエリアを見つけてください。
2. その大問2の領域の中にある「(1)」または「①」の問いを特定してください。絶対に別の（大問3や大問4にある）(1)と間違えないでください。
3. 画像文面をそのまま全文コピーして出力することはセーフティガードに触れるため【厳禁】です。必ず「〇〇に関する問題」のように1行で短く要約して確認してください。

【進め方】
① 最初の1回目のみ：
指定された問題（例：2(1)）の内容を画像から確認し、「ようこそ、チャット先生です！一緒に分からない問題を解いていきましょうね。まず、確認ですが『（ここに該当する問題のテーマや問われていることを1行で短く要約）』でよいですか？」と確認してください。
（例：「『図1の①と②に入る血管の名称を答える問題』でよいですか？」など）

② 生徒が「はい」と答えたら：
その問題のポイントを1つ短く示し、「問題の意味は分かりますか？」などと問いかけて対話をスタートしてください。

③ 返答は分かりやすく、1〜3行程度の短文で行ってください。

# 【対話ルール】
- 答えは生徒が要望しない限りギリギリまで出さず、あくまでも「正答へ導く」対話を行ってください。
- 生徒が正解したら「大正解です！この問題はクリアですね。次に進みますか？」と区切りをつけてください。"""

system_prompt = st.sidebar.text_area("システムプロンプト（AIへの指示文）", value=default_system_prompt, height=250)

# --------------------------------------------------
# 1. ヘッダーエリア
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
    "2. **「質問・問題番号入力」** に「2(1)」など問題番号のみを入力します。\n"
    "3. **「送信する」** ボタンを押すと、挽回先生と一緒に解き進められます！"
)

st.markdown("---")

# APIキー設定確認
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("APIキーの設定を確認してください。SecretsにOPENAI_API_KEYが登録されているか確認しましょう。")
    st.stop()

client = openai.OpenAI(api_key=api_key)

def encode_image(image):
    buffered = io.BytesIO()
    img = image.convert("RGB")
    img.thumbnail((1200, 1200))
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# 会話履歴表示
st.subheader("💬 チャット履歴")
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

st.markdown("---")

# 入力エリア
uploaded_file = st.file_uploader("📷 問題を貼り付け（画像をアップロード）", type=["png", "jpg", "jpeg"])
image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="貼り付けされた問題画像", use_column_width=True)

user_input = st.text_input("✍️ 質問・問題番号を入力", placeholder="例：2(1)")

# --------------------------------------------------
# 送信・AI回答エリア
# --------------------------------------------------
if st.button("送信する", type="primary"):
    if not user_input and not uploaded_file:
        st.warning("質問を入力するか、問題を貼り付けてください。")
    else:
        with st.spinner("挽回先生が問題を確認中..."):
            try:
                user_text = user_input if user_input else "この問題を教えてください。"

                api_messages = [{"role": "system", "content": system_prompt}]

                # 過去の履歴をセット
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                # 今回の入力（画像も添付）
                user_content = []
                if uploaded_file is not None:
                    base64_img = encode_image(image)
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                    })
                user_content.append({"type": "text", "text": user_text})

                api_messages.append({"role": "user", "content": user_content})

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=api_messages,
                    max_tokens=800,
                )

                assistant_reply = response.choices[0].message.content

                st.session_state.messages.append({"role": "user", "content": user_text})
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
