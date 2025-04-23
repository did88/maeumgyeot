import streamlit as st
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
from utils.gpt_emotion_tagging import get_emotion_codes_combined

# 관리자 이메일 리스트
ADMIN_EMAILS = ["wsryang@gmail.com"]

st.set_page_config(page_title="🫂 마음곁 홈", layout="centered")
st.title("🫂 마음곁")

# 로그인 확인
if "user" not in st.session_state:
    st.warning("로그인이 필요합니다. 좌측 메뉴에서 로그인해주세요.")
    st.stop()

user = st.session_state.user
email = user["email"]
uid = user["uid"]

# 🔧 사이드바 메뉴
st.sidebar.success(f"환영합니다, {email}님")
st.sidebar.page_link("main.py", label="🏠 홈")
st.sidebar.page_link("pages/6_MyPage.py", label="📈 내 감정 대시보드")
st.sidebar.page_link("pages/3_Feedback.py", label="💬 피드백")
st.sidebar.page_link("pages/4_Dream_Analysis.py", label="🌙 꿈 해석")
st.sidebar.page_link("pages/5_SelfCritic_Detector.py", label="🪞 자기비판")

if email in ADMIN_EMAILS:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔒 관리자 메뉴**")
    st.sidebar.page_link("pages/2_Admin.py", label="📊 감정 통계")
    st.sidebar.page_link("pages/2_Admin_AllData.py", label="📋 전체 활동 기록")

if st.sidebar.button("🚪 로그아웃"):
    del st.session_state.user
    st.rerun()

# Firebase 초기화
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 위로 문구 사전
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

# GPT 위로 메시지 생성
def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 감정을 공감하고 따뜻하게 위로해주는 조력자야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# 감정 코드 자동 태깅 (하이브리드 + 방어 로직 포함)
def generate_emotion_codes(text):
    return get_emotion_codes_combined(text)

# 감정 저장
def save_emotion(uid, text_input, gpt_response, emotion_codes):
    db.collection("users").document(uid).collection("emotions").add({
        "input_text": text_input,
        "emotion_codes": emotion_codes,
        "gpt_response": gpt_response,
        "timestamp": datetime.datetime.now()
    })

# 📝 감정 입력 UI
st.markdown("### 오늘의 감정을 입력해보세요 ✍️")
text_input = st.text_area("당신의 감정을 자유롭게 적어주세요")

if st.button("💌 감정 보내기"):
    if text_input.strip():
        with st.spinner("감정을 분석하고 있어요..."):
            gpt_response = generate_response(text_input)
            emotion_codes = generate_emotion_codes(text_input)
            save_emotion(uid, text_input, gpt_response, emotion_codes)

            st.markdown("#### 💬 GPT의 위로")
            top_code = emotion_codes[0] if emotion_codes else "unspecified"
            comfort = comfort_phrases.get(top_code, comfort_phrases["unspecified"])

            st.markdown(
                f"<div style='background-color:#f0f8ff; padding:15px; border-radius:10px; border:1px solid #dbeafe;'>{gpt_response}"
                f"<br><br><span style='color:#666;'>💡 {comfort}</span></div>",
                unsafe_allow_html=True
            )
            st.markdown(f"🔖 **감정 코드:** `{', '.join(emotion_codes)}`")
            st.text(f"🧪 DEBUG 감정 코드: {emotion_codes}")
    else:
        st.warning("감정을 입력해주세요.")

# 📜 감정 히스토리 출력
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
