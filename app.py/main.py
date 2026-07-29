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
