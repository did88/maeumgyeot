import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import random

# ====== Firebase 초기화 ======
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase/firebase_service_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ====== 테스트 유저 정보 ======
test_uid = "test_user_001"
test_email = "tester@example.com"

# ====== 테스트 감정 목록 ======
test_emotions = [
    {"text": "오늘 너무 지치고 외로워", "code": "sadness"},
    {"text": "좋은 일이 생겨서 기뻐!", "code": "joy"},
    {"text": "왜 아무도 나를 이해 못해?", "code": "anger"},
    {"text": "앞으로가 불안해...", "code": "anxiety"},
    {"text": "산책하고 나니까 기분이 한결 나아졌어", "code": "relief"},
]

# ====== Firestore에 데이터 삽입 ======
def insert_test_emotions():
    user_doc = db.collection("users").document(test_uid)
    user_doc.set({
        "email": test_email,
        "created_at": datetime.datetime.now(),
        "agreed_to_terms": True
    })

    for entry in test_emotions:
        emotion_doc = user_doc.collection("emotions").document()
        emotion_doc.set({
            "input_text": entry["text"],
            "emotion_code": entry["code"],
            "gpt_response": f"\"{entry['text']}\"에 공감해요. 당신의 마음을 이해하고 있어요 💛",
            "timestamp": datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 7))
        })

    print("✅ 테스트 감정 데이터가 성공적으로 삽입되었습니다.")

if __name__ == "__main__":
    insert_test_emotions()
