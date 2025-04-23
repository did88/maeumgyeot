
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(page_title="🗑️ 감정 기록 정리", layout="centered")
st.title("🗑️ 감정 기록 중 'unspecified' 삭제")

# Firebase 초기화
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

if st.button("🧹 'unspecified' 감정 코드 기록 모두 삭제"):
    count = 0
    users = db.collection("users").list_documents()
    for user_doc in users:
        uid = user_doc.id
        emotion_docs = db.collection("users").document(uid).collection("emotions").stream()
        for doc in emotion_docs:
            data = doc.to_dict()
            if "unspecified" in data.get("emotion_codes", []):
                db.collection("users").document(uid).collection("emotions").document(doc.id).delete()
                count += 1
    st.success(f"'unspecified' 감정 코드가 포함된 기록 {count}건 삭제 완료 ✅")
else:
    st.info("🧾 삭제하려면 위 버튼을 눌러주세요.")
