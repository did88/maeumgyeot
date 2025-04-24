import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
from admin_modules import (
    emotion_trends,
    combo_emotion,
    belief_shift,
    self_criticism,
    best_consolations,
)

# 관리자 이메일 목록
ADMIN_EMAILS = ["wsryang@gmail.com"]

def is_admin():
    return (
        "user" in st.session_state
        and st.session_state.user["email"] in ADMIN_EMAILS
    )

if not is_admin():
    st.error("⛔ 접근 권한이 없습니다. 관리자만 접근 가능합니다.")
    st.stop()

st.set_page_config(page_title="📊 관리자 전용 페이지", layout="wide")
st.title("📊 관리자 통합 분석 페이지")

# Firebase 연결
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 🔀 탭 선택 (모든 기능 포함)
tab = st.radio("🔎 보고 싶은 항목을 선택하세요", [
    "감정 통계",
    "복합 감정 분석",
    "고정관념 변화",
    "자기비판 분석",
    "베스트 위로 통계",
    "사용자 피드백"
])

# 각 기능 연결
if tab == "감정 통계":
    emotion_trends.run(db)

elif tab == "복합 감정 분석":
    combo_emotion.run(db)

elif tab == "고정관념 변화":
    belief_shift.run(db)

elif tab == "자기비판 분석":
    self_criticism.run(db)

elif tab == "베스트 위로 통계":
    best_consolations.run(db)

elif tab == "사용자 피드백":
    st.subheader("📬 사용자 피드백 모아보기")
    users = db.collection("users").list_documents()
    for user_doc in users:
        uid = user_doc.id
        feedbacks = (
            db.collection("users")
            .document(uid)
            .collection("feedback")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .stream()
        )
        feedback_list = list(feedbacks)
        if feedback_list:
            st.markdown(f"### 🧑 사용자: `{uid}`")
            for doc in feedback_list:
                data = doc.to_dict()
                timestamp = data.get("timestamp")
                text = data.get("text", "내용 없음")
                st.markdown(f"- 🕒 `{timestamp.strftime('%Y-%m-%d %H:%M')}`<br>✍️ {text}", unsafe_allow_html=True)
            st.markdown("---")
    st.stop()
