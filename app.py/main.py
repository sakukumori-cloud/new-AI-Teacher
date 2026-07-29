import base64
import io
import os
import openai
from PIL import Image
import streamlit as st
from streamlit_cropper import st_cropper

st.set_page_config(
    page_title="チャット先生！ - 個別指導アシスタント",
    page_icon="👩‍🏫",
    layout="centered",
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "need_crop" not in st.session_state:
    st.session_state.need_crop = False

# サイドバー
st.sidebar.title("⚙️ 画面表示・設定")
if st.sidebar.button("💬 会話履歴をリセット", use_container_width=True):
    st.session_state.messages = []
    st.session_state.need_crop = False
    st.rerun()

custom_caption = st.sidebar.text_input("サブタイトル", value="－個別指導アシスタント－")
custom_title = st.sidebar.text_input("メインタイトル", value="チャット先生！")
custom_info = st.sidebar.text_area(
    "メッセージ文章",
    value="挽回先生です！\n\n間違えた問題や解き方に自信がない問題について、一緒にやり取りしながら解決を目指します。",
    height=150
)

default_system_prompt = """あなたは個別指導のベテランの「挽回先生」です。生徒が送ってきた画像と質問をもとに、対話しながら一緒に解いていきます。

【判定ルール】
生徒が「2(1)」のように問題番号を指定してきた場合、画像から該当の問題を特定してください。
1. **問題が明確に特定できた場合**:
   - フラグキーワード `[TARGET_OK]` を文頭に付けて、「ようこそ、チャット先生です！一緒に分からない問題を解いていきましょうね。まず、確認ですが『（問いのテーマや内容を1行で短く要約）』でよいですか？」と回答してください。
2. **問題が入り組んでいて特定に自信がない場合**:
   - フラグキーワード `[NEED_CROP]` を文頭に付けて、「画像内に複数の問題があるため、該当の問題を正確に読み取れませんでした。画面下の枠を動かして、解きたい問題の周辺だけを囲んで再送信してみてください！」と優しく案内してください。"""

system_prompt = st.sidebar.text_area("システムプロンプト（AIへの指示文）", value=default_system_prompt, height=250)

# メイン画面
st.caption(custom_caption)
st.title(custom_title)
st.info(custom_info)
st.markdown("---")

# APIキーの自動読み込み（Secretsから取得）
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ secrets.toml に OPENAI_API_KEY が正しく設定されていません。")
    st.stop()

client = openai.OpenAI(api_key=api_key)

def encode_image(image):
    buffered = io.BytesIO()
    img = image.convert("RGB")
    img.thumbnail((1200, 1200))
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# チャット履歴
st.subheader("💬 チャット履歴")
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

st.markdown("---")

uploaded_file = st.file_uploader("📷 問題を貼り付け（画像をアップロード）", type=["png", "jpg", "jpeg"])
cropped_img = None

if uploaded_file is not None:
    raw_image = Image.open(uploaded_file)
    if st.session_state.need_crop:
        st.info("✂️ **解きたい問題の場所だけを枠で囲んでください：**")
        cropped_img = st_cropper(raw_image, realtime_update=True, box_color='#FF0000', aspect_ratio=None)
        if cropped_img:
            st.image(cropped_img, caption="切り抜き領域", use_column_width=True)
    else:
        st.image(raw_image, caption="全体画像", use_column_width=True)

user_input = st.text_input("✍️ 質問・問題番号を入力", placeholder="例：2(1)")

if st.button("送信する", type="primary"):
    if not user_input and not uploaded_file:
        st.warning("質問を入力するか、問題を貼り付けてください。")
    else:
        with st.spinner("挽回先生が問題を確認中..."):
            try:
                user_text = user_input if user_input else "この問題を教えてください。"
                api_messages = [{"role": "system", "content": system_prompt}]
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                user_content = []
                if uploaded_file is not None:
                    target_image = cropped_img if (st.session_state.need_crop and cropped_img is not None) else raw_image
                    base64_img = encode_image(target_image)
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

                raw_reply = response.choices[0].message.content

                if "[NEED_CROP]" in raw_reply:
                    st.session_state.need_crop = True
                    assistant_reply = raw_reply.replace("[NEED_CROP]", "").strip()
                elif "[TARGET_OK]" in raw_reply:
                    st.session_state.need_crop = False
                    assistant_reply = raw_reply.replace("[TARGET_OK]", "").strip()
                else:
                    assistant_reply = raw_reply

                st.session_state.messages.append({"role": "user", "content": user_text})
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
