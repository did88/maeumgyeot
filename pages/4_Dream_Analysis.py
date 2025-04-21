import streamlit as st
import datetime
from firebase_admin import firestore
from openai import OpenAI

st.set_page_config(page_title="🌙 꿈 해석 챗봇", layout="centered")
st.title("🌙 꿈 해석 챗봇")

# ====== 테스트용 세션 설정 (배포 시 제거) ======
if "user" not in st.session_state:
    st.session_state.user = {
        "sub": "test_user_001",
        "email": "tester@example.com"
    }

user = st.session_state.user
uid = user["sub"]

# ====== GPT 클라이언트 초기화 ======
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ====== GPT 꿈 해석 함수 (후속 질문 포함) ======
def interpret_dream(dream_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content":
             "너는 심리 분석가이자 꿈 해석 전문가야. "
             "사용자의 꿈을 상징적, 무의식적 관점에서 해석해주고, "
             "해석이 끝나면 사용자가 자신의 꿈을 더 깊이 이해할 수 있도록 2~3개의 후속 질문도 제안해줘. "
             "질문은 꿈속 인물, 감정, 상황, 현실과의 연관성에 초점을 맞춰줘."},
            {"role": "user", "content": dream_text}
        ]
    )
    return response.choices[0].message.content

# ====== UI ======
st.markdown("밤사이 꾼 꿈이 기억나시나요? 아래에 자유롭게 입력해보세요.")
dream_text = st.text_area("🌌 꿈 내용을 입력하세요", height=200, placeholder="예: 검은 강아지가 나를 쫓아왔고 나는 도망치다가 날아올랐어요...")

if st.button("🔮 꿈 해석 요청"):
    if dream_text.strip():
        with st.spinner("꿈의 상징과 무의식을 해석 중입니다..."):
            interpretation = interpret_dream(dream_text)

            # Firestore 저장
            db = firestore.client()
            db.collection("users").document(uid).collection("dreams").add({
                "input_text": dream_text,
                "gpt_response": interpretation,
                "timestamp": datetime.datetime.now()
            })

            st.success("꿈 해석이 완료되었습니다!")
            st.markdown("#### 💬 GPT의 해석 + 후속 탐색 질문")
            st.markdown(f"""
            <div style='background-color:#f5f5f5; padding:15px; border-radius:10px; color:#222;'>
                {interpretation}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("꿈 내용을 입력해주세요.")
