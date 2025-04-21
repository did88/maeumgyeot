import streamlit as st
from firebase_admin import firestore
import datetime

st.set_page_config(page_title="📝 피드백", layout="centered")
st.title("📝 마음곁 피드백 남기기")

# 로그인 확인
if "user" not in st.session_state:
    st.error("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user
uid = user["sub"]

# Firestore 연결
db = firestore.client()

# 피드백 입력 폼
st.markdown("서비스에 대한 피드백이나 제안하고 싶은 내용을 자유롭게 적어주세요.")
feedback_text = st.text_area("💬 피드백 내용", height=200)

if st.button("📩 피드백 제출"):
    if feedback_text.strip():
        db.collection("feedbacks").add({
            "uid": uid,
            "email": user["email"],
            "feedback": feedback_text,
            "timestamp": datetime.datetime.now()
        })
        st.success("피드백이 성공적으로 제출되었습니다. 감사합니다!")
    else:
        st.warning("내용을 입력해주세요.")
