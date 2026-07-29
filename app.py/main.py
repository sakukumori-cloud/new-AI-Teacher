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
        "チャット先生です！\n\n"
        "私は間違えた問題、分からない問題、解き方が自信がない問題等について、"
        "チャットをしながら解決し、弱点克服を目指します。\n\n"
        "「今、分からない！」に即、対応、あなたの学習をサポートします。"
    ),
    height=150
)

# 4. プロンプト調整機能
st.sidebar.markdown("---")
st.sidebar.subheader("🧪 AI先生の指示（プロンプト調整）")
st.sidebar.caption("先生の性格や答え方をここで直接テスト・修正できます。")

default_system_prompt = """あなたは親切で教え上手な個別指導の先生「チャット先生」です。

【重要ルール】
1. 画像が送られた場合は、まず画像内の問題テキスト、図、記号、問題番号を正確に読み取り、何についての問題か（例：岩石の性質、二次関数など）を特定してください。
2. 抽象的な精神論（「図をよく見ましょう」など）だけで終わらせず、具体的な手順・計算式・解法のポイントを明確に示してください。
3. 生徒が「答えを教えて」「答えは？」と具体的に聞いてきた場合は、焦らさずにズバリ結論や答えをわかりやすく提示した上で解説してください。
4. 生徒を否定せず、最後は前向きになれる温かい言葉で励ましてください。"""

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

# 画像エンコード関数の強化（リサイズとRGB変換による精度向上）
def encode_image(image):
    buffered = io.BytesIO()
    img = image.convert("RGB")
    img.thumbnail((1024, 1024))  # Vision API用に最適なサイズに調整
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# --------------------------------------------------
# 4. これまでの会話履歴表示
# --------------------------------------------------
st.subheader("💬 チャット履歴")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        # ユーザー発言のテキスト部分を取得して表示
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
    placeholder="例：(3)の解説をお願いします！",
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
                # ユーザーの発言（テキスト）を用意
                user_text = user_input if user_input else "この問題を教えてください。"

                # 履歴用のユーザーメッセージ構築
                user_message_for_history = {"role": "user", "content": user_text}
                
                # API送信用のメッセージリスト作成
                api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

                # 画像がある場合、今回の最新メッセージに画像をアタッチする
                if image is not None:
                    base64_image = encode_image(image)
                    current_user_content = [
                        {
                            "type": "text", 
                            "text": (
                                f"{user_text}\n\n"
                                "【厳禁指示】画像の内容をそのまま文字起こししたり、解説文をまとめ書きすることは絶対に禁止です。"
                                "画像を確認したら、問題文の文字起こしは一切出力せず、すぐ横にいる先生として「(4)のアだね！図の中の1〜4の番号は見えてるかな？」というように、50文字以内の短い問いかけだけを1文返してください。"
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

                # OpenAI APIへリクエスト (gpt-4o-mini)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=api_messages,
                    max_tokens=1000,
                )

                assistant_reply = response.choices[0].message.content

                # セッション履歴にはテキストのみを保存（画像データの累積による認識低下を防止）
                st.session_state.messages.append(user_message_for_history)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

                # 画面を更新して最新会話を表示
                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
