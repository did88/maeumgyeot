import streamlit as st
import datetime
from firebase_admin import firestore

st.set_page_config(page_title="📬 피드백", layout="centered")
st.title("📬 사용자 피드백")

# ====== 테스트용 세션 설정 (배포 시 제거) ======
if "user" not in st.session_state:
    st.session_state.user = {
        "sub": "test_user_001",
        "email": "tester@example.com"
    }

user = st.session_state.user
uid = user["sub"]

st.markdown("여러분의 피드백은 마음곁을 더 따뜻한 앱으로 성장시키는 데 큰 도움이 됩니다. 😊")

feedback = st.text_area("불편했던 점, 개선 아이디어, 하고 싶은 말 등 자유롭게 남겨주세요!")

if st.button("📤 피드백 제출"):
    if feedback.strip():
        db = firestore.client()
        db.collection("feedbacks").add({
            "uid": uid,
            "email": user["email"],
            "content": feedback.strip(),
            "timestamp": datetime.datetime.now()
        })
        st.success("소중한 피드백 감사합니다! 💛")
    else:
        st.warning("피드백 내용을 입력해주세요.")
