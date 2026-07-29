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
# 会話履歴の初期化
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# サイドバー（設定・カスタマイズエリア）
# --------------------------------------------------
st.sidebar.title("⚙️ 画面表示・設定")

# 1. 会話リセットボタン
if st.sidebar.button("💬 会話履歴をリセット", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

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
    if os.path.exists("app.py/teacher.jpg"):
        teacher_img = "app.py/teacher.jpg"
    elif os.path.exists("teacher.jpg"):
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
        "挽回先生です！\n\n"
        "間違えた問題や解き方に自信がない問題について、"
        "一緒にやり取りしながら解決を目指します。"
    ),
    height=150
)

# 4. プロンプト調整機能
st.sidebar.markdown("---")
st.sidebar.subheader("🧪 AI先生の指示（プロンプト調整）")

default_system_prompt = """あなたは個別指導のベテラン講師「挽回先生」です。生徒のすぐ横でノートを一緒に覗き込みながら、一歩ずつ対話で解いていきます。

【絶対ルール：オウム返しの禁止と「指差しヒント」】
1. 「どれが気になる？」「具体的に教えて」という丸投げの聞き返しは【完全禁止】です。
   生徒が「分からない」「ヒント」と言ったら、質問で返すのではなく、図や問題文の「見るべき注目ポイント」を先生から1つ指し示してください。

2. ヒントの出し方（具象的な指差し）
   「低気圧が発達しやすい場所＝中心の近くや前線の近く」といった知識を踏まえて、「図の中心に近い1〜4の番号はどれかな？」のように、生徒が図を探せるヒントを出してください。

3. 1回の発言は80文字以内（2〜3行）
   長文解説は一切書かず、LINEのように短文でキャッチボールをしてください。

4. 口調とマインド
   「（4）のアだね！」「よし、じゃあ図の真ん中あたりを見てみようか」といった、温かく親しみやすい先生の話し言葉（〜だね、〜かな？）で接してください。"""

system_prompt = st.sidebar.text_area(
    "システムプロンプト（AIへの指示文）",
    value=default_system_prompt,
    height=250
)

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
    "2. **「質問・問題番号入力」** に「(4)のアが分かりません」などと入力します。\n"
    "3. **「送信する」** ボタンを押すと、挽回先生と一緒に解き進められます！"
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
    img = image.convert("RGB")
    img.thumbnail((1024, 1024))
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# --------------------------------------------------
# 4. これまでの会話履歴表示
# --------------------------------------------------
st.subheader("💬 チャット履歴")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        text_content = ""
        if isinstance(msg["content"], list):
            for c in msg["content"]:
                if c.get("type") == "text":
                    text_content += c.get("text", "")
        else:
            text_content = msg["content"]
        st.chat_message("user").write(text_content)
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

st.markdown("---")

# --------------------------------------------------
# 5. ユーザー入力・アップロードエリア
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
    placeholder="例：(4)のアの解説をお願いします！",
)

# --------------------------------------------------
# 6. 送信・AI回答エリア
# --------------------------------------------------
if st.button("送信する", type="primary"):
    if not user_input and not uploaded_file:
        st.warning("質問を入力するか、問題を貼り付けてください。")
    else:
        with st.spinner("挽回先生がノートを確認中..."):
            try:
                user_text = user_input if user_input else "この問題を教えてください。"
                user_message_for_history = {"role": "user", "content": user_text}
                
                api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

                if image is not None:
                    base64_image = encode_image(image)
                    current_user_content = [
                        {
                            "type": "text", 
                            "text": (
                                f"{user_text}\n\n"
                                "【挽回先生としての会話ルール】\n"
                                "1. 文字起こしや長文解説は禁止です。\n"
                                "2. 生徒から『分からない』『ヒント』と言われたら、『どれが気になる？』と聞き返してはいけません！"
                                "必ず『図のどこに注目すればいいか』の具体的なヒントや着眼点を1つ出してください。（例：『中心の近くにある記号や、等圧線が混み合っている場所に着目してみよう。1〜4の中でどれが一番中心に近いかな？』）\n"
                                "3. 1回の発言は2〜3行（80文字以内）で、次に生徒が観察すべきポイントを短く示してください。"
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        }
                    ]
                    api_messages.append({"role": "user", "content": current_user_content})
                else:
                    api_messages.append({"role": "user", "content": user_text})

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=api_messages,
                    max_tokens=1000,
                )

                assistant_reply = response.choices[0].message.content

                st.session_state.messages.append(user_message_for_history)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
