import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# ====== Firebase 초기화 ======
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase/firebase_service_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ====== 감정 저장 함수 ======
def save_emotion(uid, text_input, gpt_response, emotion_code="unspecified"):
    doc_ref = db.collection("users").document(uid).collection("emotions").document()
    doc_ref.set({
        "input_text": text_input,
        "emotion_code": emotion_code,
        "gpt_response": gpt_response,
        "timestamp": datetime.datetime.now()
    })

# ====== 감정 기록 불러오기 ======
def get_emotion_history(uid):
    docs = db.collection("users").document(uid).collection("emotions")\
        .order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return [doc.to_dict() for doc in docs]
