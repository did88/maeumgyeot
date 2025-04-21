import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt

# ✅ 관리자 이메일 목록
ADMIN_EMAILS = ["wsryang@gmail.com"]

def is_admin():
    return (
        "user" in st.session_state and
        st.session_state.user["email"] in ADMIN_EMAILS
    )

# 로그인 및 관리자 확인
if "user" not in st.session_state or not is_admin():
    st.error("⛔ 접근 권한이 없습니다. 관리자만 접근 가능합니다.")
    st.stop()

# 로그아웃 버튼
with st.sidebar:
    st.caption(f"👑 관리자: {st.session_state.user['email']}")
    if st.button("🚪 로그아웃"):
        del st.session_state.user
        st.experimental_rerun()

st.title("📊 감정 통계 대시보드")

# ✅ Firebase 연결
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ✅ 감정 데이터 수집
def fetch_all_emotions():
    all_data = []
    users = db.collection("users").list_documents()
    for user_doc in users:
        uid = user_doc.id
        emotions_ref = user_doc.collection("emotions").stream()
        for doc in emotions_ref:
            d = doc.to_dict()
            all_data.append({
                "uid": uid,
                "text": d.get("input_text", ""),
                "emotion": d.get("emotion_code", "unspecified"),
                "timestamp": d.get("timestamp")
            })
    return pd.DataFrame(all_data)

df = fetch_all_emotions()

if df.empty:
    st.info("아직 감정 데이터가 없습니다.")
    st.stop()

# ✅ 날짜 변환
df["date"] = pd.to_datetime(df["timestamp"]).dt.date

# ✅ 감정 코드별 분포 시각화
st.subheader("💬 감정 코드 분포")
emotion_counts = df["emotion"].value_counts()

st.bar_chart(emotion_counts)

# ✅ 날짜별 감정 수
st.subheader("📆 날짜별 감정 입력 수")
daily_counts = df.groupby("date").size()
st.line_chart(daily_counts)

# ✅ 원한다면 raw 데이터도 표시
with st.expander("📝 원본 감정 데이터 보기"):
    st.dataframe(df.sort_values(by="timestamp", ascending=False))
