import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# ✅ Firebase 초기화
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ✅ 로그인 확인
if "user" not in st.session_state:
    st.error("로그인 후 이용해 주세요.")
    st.stop()

uid = st.session_state.user["uid"]

st.set_page_config(page_title="🧩 마음 깨기 질문 회고", layout="centered")
st.title("🧩 마음 깨기 질문 회고")
st.markdown("그동안 생성된 마음 깨기 질문들을 모아서 회고해보세요. 사고의 전환을 이끌어준 질문들이에요.")

# ✅ 데이터 수집
records = []
docs = db.collection("users").document(uid).collection("emotions").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
for doc in docs:
    d = doc.to_dict()
    if d.get("wakeup_question"):
        records.append({
            "날짜": d["timestamp"].strftime("%Y-%m-%d %H:%M"),
            "감정": d["input_text"],
            "마음 깨기 질문": d["wakeup_question"]
        })

if not records:
    st.info("아직 마음 깨기 질문이 생성된 기록이 없어요.")
else:
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("🧠 질문만 모아보기")
    for r in records:
        st.markdown(f"- 🧩 {r['마음 깨기 질문']}")
