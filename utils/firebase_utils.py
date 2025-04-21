import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 초기화 (한 번만)
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

def get_emotion_history(uid):
    docs = (
        db.collection("users")
          .document(uid)
          .collection("emotions")
          .order_by("timestamp", direction=firestore.Query.DESCENDING)
          .stream()
    )
    return [doc.to_dict() for doc in docs]
