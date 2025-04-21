import streamlit as st
from firebase_admin import firestore
from openai import OpenAI
import datetime

st.set_page_config(page_title="🌙 꿈 해석", layout="centered")
st.title("🌙 꿈 해석 챗봇")

# 로그인 확인
if "user" not in st.session_state:
    st.error("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user
uid = user["sub"]

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
db = firestore.client()

def interpret_dream(dream_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content":
             "너는 꿈을 심리학적으로 해석해주는 상담가야. 사용자의 꿈 내용을 바탕으로 상징과 무의식을 해석해줘. "
             "그리고 마지막에는 사용자가 더 깊이 탐색할 수 있도록 질문을 1~2개 던져줘."},
            {"role": "user", "content": dream_text}
        ]
    )
    return response.choices[0].message.content

st.markdown("기억나는 꿈이 있다면 자유롭게 적어보세요. 당신의 무의식을 함께 살펴볼게요.")
dream_input = st.text_area("💤 꿈 내용을 적어주세요", height=200)

if st.button("🔮 꿈 해석 요청"):
    if dream_input.strip():
        with st.spinner("당신의 꿈을 해석하는 중이에요..."):
            result = interpret_dream(dream_input)

            db.collection("users").document(uid).collection("dreams").add({
                "input_text": dream_input,
                "gpt_response": result,
                "timestamp": datetime.datetime.now()
            })

            st.success("꿈 해석이 완료되었습니다!")
            st.markdown("#### 💬 GPT의 꿈 해석 및 질문")
            st.markdown(f"""
<div style='background-color:#f0f8ff; padding:15px 20px; border-radius:10px; border: 1px solid #dbeafe; color:#222;'>
{result}
</div>
""", unsafe_allow_html=True)
    else:
        st.warning("꿈 내용을 입력해주세요.")
