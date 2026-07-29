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

# 1. 会話リセットボタン
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

# DifyのプロンプトをStreamlit用に最適化
default_system_prompt = """あなたは個別指導のベテランの「挽回先生」です。生徒と対話しながら生徒が送ってきた分からない問題、解き方に自信がない問題などを生徒と一緒に解いていきます。

【進め方】
① 最初の1回目のみ、送られてきた情報をもとに「ようこそ、チャット先生です！一緒に分からない問題を解いていきましょうね。まず、分からない問題を確認します。問題は『〜』でよいですか？」と確認してください。
（※この確認の挨拶は、会話の開始時の「最初の1回」だけであり、途中で話題が変わっても絶対に繰り返さないこと）

② 問題が確認できたら、内容の概略を1〜2行で示し「問題の意味は分かりますか？」または図の見るべきポイントを短く問いかけます。

③ 以降は生徒との対話で学習を進め、正答へ導きます。生徒が正しい根拠や番号（例：「3」）を答えたら、無駄に話を延ばさず「大正解です！この問題はこれでクリアですね！次に進みますか？」と区切りをつけてください。

# 【言葉選び・対話の最重要ルール】
- 送られてきた文字や図の情報以外の「勝手な補足（存在しない言葉を付け加えること）」は絶対禁止です。
- 生徒への質問は分かりやすく、簡潔に、1〜2行でまとめて行ってください。
- 説明を行う場合、その説明内容区切りごとに「ここまで分かりますか？」と生徒に問いかけましょう。
- 答えは生徒が要望しない限りギリギリまで出さず、あくまでも「正答へ導く」のが仕事と考えて臨んでください。
- 正解に達したら、無理に次の難題を被せず、達成感を認めて次の問題に進むか生徒に聞いてください。"""

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
    "2. **「質問・問題番号入力」** に「(4)のアが分かりません」などと入力します。\n"
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

user_input = st.text_input("✍️ 質問・問題番号を入力", placeholder="例：(4)のアの解説をお願いします！")

# --------------------------------------------------
# 送信・AI回答エリア（2ノード分離処理）
# --------------------------------------------------
if st.button("送信する", type="primary"):
    if not user_input and not uploaded_file:
        st.warning("質問を入力するか、問題を貼り付けてください。")
    else:
        with st.spinner("挽回先生がノートを確認中..."):
            try:
                user_text = user_input if user_input else "この問題を教えてください。"
                
                # 【ノード1：裏側での画像解析・状況整理処理】
                extracted_image_context = ""
                if image is not None:
                    base64_image = encode_image(image)
                    ocr_prompt = [
                        {
                            "type": "text",
                            "text": (
                                "この問題画像の内容を解析し、挽回先生に伝えるための要約データを作成してください。\n"
                                "1. 問題番号と問題文の概要（例：(4)のア 低気圧が発達しやすい地点を選ぶ問題など）\n"
                                "2. 図の内容（例：日本付近の天気図、1〜4の選択肢の位置、低気圧や等圧線の状態）\n"
                                "※「読めない」とは回答せず、目視できる情報を箇条書きで簡潔に整理してください。"
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
                        max_tokens=800
                    )
                    extracted_image_context = f"\n\n【画像から読み取った問題の整理データ】:\n{ocr_response.choices[0].message.content}"

                # 【ノード2：挽回先生対話ノード】
                current_prompt = f"{user_text}{extracted_image_context}"
                
                api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                api_messages.append({"role": "user", "content": current_prompt})

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=api_messages,
                    max_tokens=800,
                )

                assistant_reply = response.choices[0].message.content

                # セッション履歴（見た目）にはテキストのみを保存
                st.session_state.messages.append({"role": "user", "content": user_text})
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
