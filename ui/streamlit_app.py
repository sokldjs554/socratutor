"""SocraTutor 채팅 데모 UI.

실행: streamlit run ui/streamlit_app.py  (API 서버가 켜져 있어야 한다)
"""

import requests
import streamlit as st

API = "http://localhost:8000"

st.set_page_config(page_title="SocraTutor", page_icon="🏛️")
st.title("🏛️ SocraTutor")
st.caption("정답을 바로 알려주지 않는 소크라테스식 영어 튜터")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("영어 문법에 대해 물어보세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            resp = requests.post(
                f"{API}/chat", json={"user_id": 1, "message": prompt}, timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
        st.markdown(data["reply"])
        u = data["usage"]
        st.caption(
            f"토큰 {u['input_tokens']}+{u['output_tokens']} · {u['latency_ms']}ms"
        )
    st.session_state.messages.append({"role": "assistant", "content": data["reply"]})
