import streamlit as st
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
from utils.gpt_emotion_tagging import get_emotion_codes_combined

# ✅ 관리자 이메일 (필요 시 사용)
ADMIN_EMAILS = ["wsryang@gmail.com"]

# ✅ 페이지 설정
st.set_page_config(page_title="🫂 마음곁 홈", layout="centered")

# ✅ 로그인 확인
if not st.session_state.get("user"):
    st.markdown("<h1 style='display: flex; align-items: center; gap: 10px;'>🤗 마음곁</h1>", unsafe_allow_html=True)
    st.info("""
    ### 👋 환영합니다!
    **마음곁**은 감정을 기록하고 위로를 받을 수 있는 심리 지원 앱입니다.  
    GPT 기반으로 감정을 나누고, 감정 흐름을 돌아보며 자신을 더 이해할 수 있도록 도와드려요.

    🔐 먼저 로그인이 필요합니다.  
    👉 **좌측 메뉴에서 로그인** 또는 **회원가입**을 진행해 주세요.
    """)
    st.stop()

# ✅ 로그인된 사용자 정보
user = st.session_state.user
email = user["email"]
uid = user["uid"]

# ✅ Firebase 초기화
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
    try:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    except ValueError as e:
        st.error("Firebase 인증서 초기화에 실패했습니다. 관리자에게 문의해주세요.")
        st.stop()

# ✅ Firestore 클라이언트
db = firestore.client()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ✅ 감정 코드별 위로 문구
comfort_phrases = {
    "기쁨": "😊 기쁨은 소중한 에너지예요.",
    "슬픔": "😢 슬플 땐 충분히 울어도 괜찮아요.",
    "분노": "😠 화가 날 땐 감정을 억누르지 마세요.",
    "불안": "😥 불안은 마음의 준비일지도 몰라요.",
    "외로움": "😔 외로움을 느끼는 건 당연해요. 함께 있어줄게요.",
    "사랑": "😍 누군가를 사랑한다는 건 참 멋진 일이에요.",
    "무감정/혼란": "😶 혼란스러울 땐 잠시 멈추고 자신을 바라봐요.",
    "지루함": "🥱 지루함도 때론 필요한 감정이에요.",
    "후회/자기비판": "💭 너무 자신을 몰아붙이지 말아요.",
    "unspecified": "💡 어떤 감정이든 소중해요. 표현해줘서 고마워요."
}

# ✅ GPT 응답 생성
def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 감정을 공감하고 따뜻하게 위로해주는 조력자야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ✅ 감정 코드 태깅
def generate_emotion_codes(text):
    return get_emotion_codes_combined(text)

# ✅ 감정 저장
def save_emotion(uid, text_input, gpt_response, emotion_codes):
    db.collection("users").document(uid).collection("emotions").add({
        "input_text": text_input,
        "emotion_codes": emotion_codes,
        "gpt_response": gpt_response,
        "timestamp": datetime.datetime.now()
    })

# ✅ 감정 입력 섹션
st.markdown("### 오늘의 감정을 입력해보세요 ✍️")
text_input = st.text_area("당신의 감정을 자유롭게 적어주세요")

if st.button("💌 감정 보내기"):
    if text_input.strip():
        with st.spinner("감정을 분석하고 있어요..."):
            gpt_response = generate_response(text_input)
            emotion_codes = generate_emotion_codes(text_input)
            save_emotion(uid, text_input, gpt_response, emotion_codes)

            st.markdown("#### 💬 GPT의 위로")
            if emotion_codes:
                comfort_lines = [f"💡 {comfort_phrases.get(code, '표현해줘서 고마워요.')}" for code in emotion_codes]
                comfort = "<br>".join(comfort_lines)
            else:
                comfort = comfort_phrases["unspecified"]

            st.markdown(
                f"<div style='background-color:#f0f8ff; padding:15px; border-radius:10px; border:1px solid #dbeafe;'>{gpt_response}"
                f"<br><br><span style='color:#666;'>{comfort}</span></div>",
                unsafe_allow_html=True
            )
            st.markdown(f"🔖 **감정 코드:** `{', '.join(emotion_codes)}`")
            st.text(f"🧪 DEBUG 감정 코드: {emotion_codes}")
    else:
        st.warning("감정을 입력해주세요.")

# ✅ 감정 히스토리 출력
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("### 📜 내 감정 히스토리")

docs = (
    db.collection("users")
    .document(uid)
    .collection("emotions")
    .order_by("timestamp", direction=firestore.Query.DESCENDING)
    .stream()
)

for doc in docs:
    d = doc.to_dict()
    ts = d["timestamp"].strftime("%Y-%m-%d %H:%M")
    codes = ", ".join(d.get("emotion_codes", ["unspecified"]))
    st.markdown(
        f"<div style='border:1px solid #ddd; padding:15px; margin-bottom:15px; border-radius:10px; background:#fff9;'>"
        f"🗓️ <b>{ts}</b><br>"
        f"<b>📝 감정:</b> {d['input_text']}<br>"
        f"<b>🏷️ 감정 코드:</b> {codes}<br>"
        f"<b>🤖 GPT의 위로:</b> {d['gpt_response']}</div>",
        unsafe_allow_html=True
    )
