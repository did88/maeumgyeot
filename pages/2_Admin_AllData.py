import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# 관리자 이메일
ADMIN_EMAILS = ["wsryang@gmail.com"]

def is_admin():
    return (
        "user" in st.session_state and
        st.session_state.user["email"] in ADMIN_EMAILS
    )

# 로그인 및 권한 확인
if "user" not in st.session_state or not is_admin():
    st.error("⛔ 접근 권한이 없습니다. 관리자만 접근 가능합니다.")
    st.stop()

# 로그아웃 버튼
with st.sidebar:
    st.caption(f"👑 관리자: {st.session_state.user['email']}")
    if st.button("🚪 로그아웃"):
        del st.session_state.user
        st.rerun()

st.title("📋 전체 사용자 활동 대시보드")

# Firebase 초기화
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 사용자 uid 목록 가져오기
users = db.collection("users").list_documents()

# 통합 데이터 수집
all_data = []
for user_doc in users:
    uid = user_doc.id

    # 각 컬렉션별로 데이터 조회
    for col in ["emotions", "dreams", "self_critic", "feedback"]:
        try:
            docs = db.collection("users").document(uid).collection(col).stream()
            for d in docs:
                entry = d.to_dict()
                all_data.append({
                    "uid": uid,
                    "type": col,
                    "input_text": entry.get("input_text") or entry.get("text", ""),
                    "gpt_response": entry.get("gpt_response", ""),
                    "timestamp": entry.get("timestamp")
                })
        except Exception as e:
            st.warning(f"{uid}의 {col} 불러오기 실패: {e}")

# DataFrame으로 정리
if all_data:
    df = pd.DataFrame(all_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp", ascending=False)

    st.dataframe(df, use_container_width=True)

    # 통계 요약
    st.subheader("📊 활동 유형별 문서 수")
    st.bar_chart(df["type"].value_counts())

    st.subheader("📅 날짜별 전체 입력 수")
    daily = df.groupby(df["timestamp"].dt.date).size()
    st.line_chart(daily)
else:
    st.info("아직 사용자 활동 데이터가 없습니다.")
