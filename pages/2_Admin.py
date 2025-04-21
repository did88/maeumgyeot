import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

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

st.title("📊 관리자 전용 페이지")

# Firebase 연결
if not firebase_admin._apps:
    try:
        firebase_config = dict(st.secrets["firebase"])
        firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase 인증 실패: {e}")
        st.stop()

db = firestore.client()

# 예시: 모든 사용자 감정 데이터 불러오기
st.subheader("📋 모든 감정 기록")

try:
    users_ref = db.collection("users").list_documents()
    for user_doc in users_ref:
        uid = user_doc.id
        emotions = (
            db.collection("users")
            .document(uid)
            .collection("emotions")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(3)
            .stream()
        )
        st.markdown(f"#### 🧑 사용자: {uid}")
        for doc in emotions:
            data = doc.to_dict()
            st.write(f"- 🕒 {data['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            st.write(f"  - 감정: {data['input_text']}")
            st.write(f"  - GPT 응답: {data['gpt_response']}")
except Exception as e:
    st.error(f"데이터 불러오기 실패: {e}")
