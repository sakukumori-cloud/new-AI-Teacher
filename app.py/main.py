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

# 会話履歴・画像読み取り記憶の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "image_context" not in st.session_state:
    st.session_state.image_context = ""

# --------------------------------------------------
# サイドバー（設定・カスタマイズエリア）
# --------------------------------------------------
st.sidebar.title("⚙️ 画面表示・設定")

# 1. 会話リセットボタン
if st.sidebar.button("💬 会話履歴をリセット", use_container_width=True):
    st.session_state.messages = []
    st.session_state.image_context = ""
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

default_system_prompt = """あなたは個別指導のベテランの「挽回先生」です。生徒と対話しながら生徒が送ってきた分からない問題、解き方に自信がない問題などを生徒と一緒に解いていきます。

【進め方】
① 最初の1回目のみ、送られてきた情報をもとに「ようこそ、チャット先生です！一緒に分からない問題を解いていきましょうね。まず、分からない問題を確認します。問題は『〜』でよいですか？」と確認してください。
（※この確認の挨拶は、会話の開始時の「最初の1回」だけであり、途中で話題が変わっても絶対に繰り返さないこと）

② 問題が確認できたら、画像に書かれている問題の要点や問われている内容を短く示し「問題の意味は分かりますか？」または図の注目ポイントを短く問いかけます。

③ 以降は生徒との対話で学習を進め、正答へ導きます。生徒が正解を答えたら「大正解です！この問題はこれでクリアですね！次に進みますか？」と区切りをつけてください。

# 【絶対ルール】
- 「画像が読めない」「テキストで教えてほしい」などの言い訳は絶対禁止です。提供されている問題データをもとに自信を持って指導してください。
- 勝手な推測で存在しない選択肢や言葉を作り出さないでください。
- 「素晴らしい要約ですね」などの大げさな相槌は避け、自然な先生の言葉で話してください。
- 返答や質問は分かりやすく、簡潔に1〜3行程度で行ってください。"""

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
    "2. **「質問・問題番号入力」** に「(1)が分かりません」などと入力します。\n"
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
        text_content = msg["content"] if isinstance(msg["content"], str) else ""
        st.chat_message("user").write(text_content)
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

st.markdown("---")

# 入力エリア
uploaded_file = st.file_uploader("📷 問題を貼り付け（画像をアップロード）", type=["png", "jpg", "jpeg"])
image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="貼り付けされた問題画像", use_column_width=True)

user_input = st.text_input("✍️ 質問・問題番号を入力", placeholder="例：(1)の解説をお願いします！")

# --------------------------------------------------
# 送信・AI回答エリア
# --------------------------------------------------
if st.button("送信する", type="primary"):
    if not user_input and not uploaded_file and not st.session_state.image_context:
        st.warning("質問を入力するか、問題を貼り付けてください。")
    else:
        with st.spinner("挽回先生がノートを確認中..."):
            try:
                user_text = user_input if user_input else "この問題を教えてください。"
                
                # 新しい画像がアップロードされた場合のみ、高精度OCRを実行してセッションに保存
                if image is not None and uploaded_file is not None:
                    base64_image = encode_image(image)
                    ocr_prompt = [
                        {
                            "type": "text",
                            "text": (
                                "【絶対命令：厳密文字起こし】\n"
                                "この画像に見える文字、問題番号、図の文字、選択肢、穴埋め番号などをすべて正確に読み取ってください。\n"
                                "「読めない」「要約する」は禁止です。画像の中にある文章と図の情報をそのまま全て文字化してください。"
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                    ocr_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": ocr_prompt}],
                        max_tokens=1000
                    )
                    # 読み取った画像をずっと記憶させておく
                    st.session_state.image_context = f"\n\n【現在参照中の問題画像データ】:\n{ocr_response.choices[0].message.content}"

                # 生徒の発言に、常に保持された画像データを付与してAIに渡す
                current_prompt = f"{user_text}{st.session_state.image_context}"
                
                api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                api_messages.append({"role": "user", "content": current_prompt})

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=api_messages,
                    max_tokens=800,
                )

                assistant_reply = response.choices[0].message.content

                # 画面上の対話履歴には見やすいテキストのみ保存
                st.session_state.messages.append({"role": "user", "content": user_text})
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
