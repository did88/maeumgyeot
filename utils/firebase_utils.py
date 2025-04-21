import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 초기화 (한 번만)
if not firebase_admin._apps:
    try:
        firebase_config = dict(st.secrets["firebase"])
        raw_key = firebase_config.get("private_key", "")
        key = raw_key.replace("\\n", "\n").strip()
        lines = [line.lstrip() for line in key.splitlines()]
        firebase_config["private_key"] = "\n".join(lines)
        cred = credentials.Certificate(firebase_config)
    except Exception as e:
        st.error(f"Firebase 인증 실패: {e}")
        st.stop()
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_emotion_history(uid):
    docs = (
        db.collection("users")
          .document(uid)
          .collection("emotions")
          .order_by("timestamp", direction=firestore.Query.DESCENDING)
          .stream()
    )
    return [doc.to_dict() for doc in docs]
