import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.oauth2 import id_token
from google.auth.transport import requests
import openai
import datetime
import json

# ====== 설정 ======
# Firebase 인증 키
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_service_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# OpenAI API 키
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ====== 유틸 함수 ======
def verify_token(token):
    try:
        info = id_token.verify_oauth2_token(token, requests.Request(), st.secrets["GOOGLE_CLIENT_ID"])
        return info
    except Exception as e:
        return None

def save_emotion(uid, text_input, gpt_response, emotion_code="unspecified"):
    doc_ref = db.collection("users").document(uid).collection("emotions").document()
    doc_ref.set({
        "input_text": text_input,
        "emotion_code": emotion_code,
        "gpt_response": gpt_response,
        "timestamp": datetime.datetime.now()
    })

def generate_response(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 감정에 공감하고 따뜻하게 위로해주는 조력자야."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message["content"]

# ====== UI ======
st.set_page_config(page_title="마음곁", layout="centered")
st.title("🫂 마음곁: 감정 위로 챗봇")

if "user" not in st.session_state:
    st.info("구글 계정으로 로그인해주세요.")
    with st.form("login_form"):
        token_input = st.text_input("Google ID Token (테스트용 입력)", type="password")
        submitted = st.form_submit_button("로그인")
        if submitted:
            user_info = verify_token(token_input)
            if user_info:
                st.session_state.user = user_info
                st.success(f"{user_info['email']}님 환영합니다!")
            else:
                st.error("유효하지 않은 토큰입니다.")
else:
    user = st.session_state.user
    st.success(f"{user['email']}님, 오늘의 감정을 입력해보세요 ✨")

    text_input = st.text_area("당신의 감정을 적어주세요")
    if st.button("전송"):
        if text_input.strip():
            with st.spinner("감정을 공감하고 있어요..."):
                gpt_response = generate_response(text_input)
                save_emotion(user['sub'], text_input, gpt_response)
                st.markdown("#### 💬 GPT의 위로")
                st.write(gpt_response)
        else:
            st.warning("감정을 입력해주세요.")

    st.markdown("---")
    st.markdown("### 📜 내 감정 히스토리")
    docs = db.collection("users").document(user['sub']).collection("emotions").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    for doc in docs:
        data = doc.to_dict()
        st.markdown(f"**날짜:** {data['timestamp'].strftime('%Y-%m-%d %H:%M')}\n\n**감정:** {data['input_text']}\n\n**GPT:** {data['gpt_response']}")
        st.markdown("---")
