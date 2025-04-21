import streamlit as st
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# 로그인 여부 확인
if "user" not in st.session_state:
    st.warning("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user
uid = user["uid"]  # ✅ sub → uid

# Firebase 연결
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("💬 피드백 보내기")
feedback = st.text_area("서비스에 대한 의견, 개선사항, 하고 싶은 말 등 자유롭게 적어주세요.")

if st.button("📤 피드백 제출"):
    if feedback.strip():
        db.collection("users").document(uid).collection("feedback").add({
            "text": feedback,
            "timestamp": datetime.datetime.now()
        })
        st.success("피드백이 제출되었습니다. 감사합니다!")
    else:
        st.warning("피드백 내용을 입력해주세요.")
