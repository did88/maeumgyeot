import streamlit as st
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI

st.set_page_config(page_title="🫂 마음곁", layout="centered")
st.markdown(
    "<h2 style='text-align:center; color:#4a4a4a;'>🫂 마음곁</h2>"
    "<p style='text-align:center; color:#888;'>당신의 마음, 곁에 머물다 💛</p>"
    "<hr style='margin-top: 0;'>",
    unsafe_allow_html=True
)

# ✅ 로그인 확인
if "user" not in st.session_state:
    st.warning("로그인이 필요합니다. 좌측 메뉴에서 '로그인' 페이지로 이동해주세요.")
    st.stop()

# ✅ 로그아웃 버튼 (최신 Streamlit 버전 대응)
with st.sidebar:
    st.caption(f"👤 {st.session_state.user['email']}")
    if st.button("🚪 로그아웃"):
        del st.session_state.user
        st.success("로그아웃 되었습니다.")
        st.rerun()  # ✅ 최신 Streamlit 방식 (이전: st.experimental_rerun)

user = st.session_state.user
uid = user["uid"]

# ✅ Firebase 초기화
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
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ✅ GPT 응답 함수
def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 감정을 공감하고 따뜻하게 위로해주는 조력자야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ✅ 감정 저장 함수
def save_emotion(uid, text_input, gpt_response, emotion_code="unspecified"):
    db.collection("users").document(uid).collection("emotions").add({
        "input_text": text_input,
        "emotion_code": emotion_code,
        "gpt_response": gpt_response,
        "timestamp": datetime.datetime.now()
    })

# ✅ 감정 코드별 위로 문구
comfort_phrases = {
    "joy": "😊 기쁨은 소중한 에너지예요.",
    "sadness": "😢 슬플 땐 충분히 울어도 괜찮아요.",
    "anger": "😠 화가 날 땐 감정을 억누르지 마세요.",
    "anxiety": "😥 불안은 마음의 준비일지도 몰라요.",
    "relief": "😌 나 자신에게 수고했다고 말해주세요.",
    "unspecified": "💭 어떤 감정이든 소중해요. 표현해줘서 고마워요."
}

# ✅ 감정 입력 영역
st.success(f"{user['email']}님, 오늘의 감정을 입력해보세요 ✨")
text_input = st.text_area("당신의 감정을 자유롭게 적어주세요")

if st.button("💌 감정 보내기"):
    if text_input.strip():
        with st.spinner("감정을 공감하고 있어요..."):
            gpt_response = generate_response(text_input)
            save_emotion(uid, text_input, gpt_response)
            st.markdown("#### 💬 GPT의 위로", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background-color:#f0f8ff; padding:15px; border-radius:10px; "
                f"border:1px solid #dbeafe;'>{gpt_response}"
                f"<br><br><span style='color:#666;'>💡 {comfort_phrases['unspecified']}</span>"
                "</div>",
                unsafe_allow_html=True
            )
    else:
        st.warning("감정을 입력해주세요.")

# ✅ 감정 히스토리 표시
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
    st.markdown(
        f"<div style='border:1px solid #ddd; padding:15px; margin-bottom:15px; "
        f"border-radius:10px; background:#fff9;'>🗓️ <b>{ts}</b><br>"
        f"<b>📝 감정:</b> {d['input_text']}<br>"
        f"<b>🤖 GPT의 위로:</b> {d['gpt_response']}</div>",
        unsafe_allow_html=True
    )
