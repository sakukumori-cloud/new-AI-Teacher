import base64
import io
import os
import openai
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="Alsensei - AI個別指導",
    page_icon="👩‍🏫",
    layout="centered",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# サイドバー設定
st.sidebar.title("⚙️ 設定 & ガイド")
if st.sidebar.button("💬 会話履歴をリセット", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 上手に質問するコツ")
st.sidebar.markdown(
    "1. **全体像を写す**: 図表やグラフ、問題文全体が含まれるように撮影・スクショしてください。\n"
    "2. **質問を具体的に**: 単に「2(1)」だけでなく、「図を見ながら、2(1)の解き方を教えて」のように伝えると精度が上がります。"
)

# システムプロンプト（挽回先生のキャラクター設定）
default_system_prompt = """あなたは優しく分かりやすい個別指導のベテラン講師「挽回先生」です。
生徒がアップロードした問題の画像（図表・文章を含む全体像）と質問をもとに指導します。

【厳守ルール】
1. 「〜でよいですか？」といった確認の質問は一切禁止。即座に分かりやすい解説を始めること。
2. 画像内の図やグラフ、文章をしっかりと読み取り、正確な答えと「なぜそうなるのか」のプロセスを丁寧に教えること。
3. 中学生にもわかりやすい身近な例えや、暗記のコツも交えて解説すること。
"""

system_prompt = st.sidebar.text_area("システムプロンプト（AIへの指示文）", value=default_system_prompt, height=220)

# メイン画面
st.caption("－個別指導アシスタント－")
st.title("AI Teachers - 挽回先生")
st.info("わからない問題の画像（図や文章全体）をアップロードし、解いてほしい問題番号を質問してください。")
st.markdown("---")

api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ secrets.toml に OPENAI_API_KEY が正しく設定されていません。")
    st.stop()

client = openai.OpenAI(api_key=api_key)

def encode_image(image):
    buffered = io.BytesIO()
    img = image.convert("RGB")
    # 高画質を維持しつつ、大きすぎる場合はAPI制限用に適度に抑える（最大1600px）
    img.thumbnail((1600, 1600))
    img.save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# チャット履歴の表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], list):
            for content_item in msg["content"]:
                if content_item.get("type") == "text":
                    st.write(content_item["text"])
                elif content_item.get("type") == "image_url":
                    st.info("📷 [送信された画像]")
        else:
            st.write(msg["content"])

# ファイルアップロード（画面下部）
uploaded_file = st.file_uploader("📷 問題の画像をアップロード（全体像）", type=["png", "jpg", "jpeg"])
if uploaded_file is not None:
    image_preview = Image.open(uploaded_file)
    st.image(image_preview, caption="アップロード画像プレビュー", use_column_width=True)

# チャット入力欄
user_query = st.chat_input("例：図を見ながら、2(1)の答えと解説を教えて")

if user_query:
    user_content_api = []
    current_image = None
    
    if uploaded_file is not None:
        current_image = Image.open(uploaded_file)
        base64_img = encode_image(current_image)
        user_content_api.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
        })
    
    user_content_api.append({"type": "text", "text": user_query})

    # 画面表示用のメッセージ履歴に追加
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        if uploaded_file is not None:
            st.image(current_image, width=300)
        st.write(user_query)

    # AIからの応答生成
    with st.spinner("挽回先生が解答と解説を作成中..."):
        try:
            api_messages = [{"role": "system", "content": system_prompt}]
            
            for m in st.session_state.messages[:-1]:
                api_messages.append({"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else "画像を送信しました"})
            
            api_messages.append({"role": "user", "content": user_content_api})

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=api_messages,
                max_tokens=1500,
            )

            assistant_reply = response.choices[0].message.content

            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            with st.chat_message("assistant"):
                st.write(assistant_reply)

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
