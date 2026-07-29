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

【最重要ルール】
- 添付された画像を必ず注意深く観察し、画像に実際に書かれている具体語（例：消化管、血管、器官名、選択肢ア〜オなど）を必ず使って回答してください。
- 抽象的な表現（「与えられた条件」「計算を行う問題」「図の情報」など）で誤魔化すことは絶対に禁止です。

【進め方】
① 最初の1回目のみ：
送られてきた画像から生徒が指定した問題（例：2(1)）の【実際の問いの文】を読み取り、「ようこそ、チャット先生です！一緒に分からない問題を解いていきましょうね。まず、分からない問題を確認します。問題は『（ここに画像から読み取った具体的な問題文を入れる）』でよいですか？」と確認してください。

② 生徒が「はい」と答えたら：
画像の中の具体的な注目ポイント（図の名称や文の空欄など）を1つ挙げて、「問題の意味は分かりますか？」または「どの選択肢だと思う？」と短く問いかけて対話を始めてください。

③ 返答は分かりやすく、1〜3行程度の短文で行ってください。"""

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
    "2. **「質問・問題番号入力」** に「2(1)をお願いします」などと入力します。\n"
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
    img.thumbnail((1024, 1024))
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

user_input = st.text_input("✍️ 質問・問題番号を入力", placeholder="例：2(1)をお願いします！")

# --------------------------------------------------
# 送信・AI回答エリア
# --------------------------------------------------
if st.button("送信する", type="primary"):
    if not user_input and not uploaded_file:
        st.warning("質問を入力するか、問題を貼り付けてください。")
    else:
        with st.spinner("挽回先生がノートを確認中..."):
            try:
                user_text = user_input if user_input else "この問題を教えてください。"

                # APIに送るメッセージ配列を作成
                api_messages = [{"role": "system", "content": system_prompt}]
                
                # 過去の会話履歴を追加
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                # 画像がある場合は、今回送信する最新メッセージに画像を直接添えてGPT-4oに渡す
                if image is not None:
                    base64_image = encode_image(image)
                    current_content = [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                else:
                    current_content = user_text

                api_messages.append({"role": "user", "content": current_content})

                # GPT-4o（高精度Visionモデル）を実行
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=api_messages,
                    max_tokens=800,
                )

                assistant_reply = response.choices[0].message.content

                # 履歴にはテキストのみを追加保存
                st.session_state.messages.append({"role": "user", "content": user_text})
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
