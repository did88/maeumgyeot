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

# Firebase init with key cleanup
if not firebase_admin._apps:
    try:
        firebase_config = dict(st.secrets["firebase"])
        # Strip surrounding whitespace/newlines
        pk = firebase_config.get("private_key", "").strip()
        # Replace literal '
' sequences with actual newlines
        if "\n" in pk:
            pk = pk.replace("\n", "\n")  # preserve Python string form
            pk = pk.replace("\\n", "\n")
            pk = pk.replace("\n", "
")
        # Remove leading spaces for each line
        lines = [line.lstrip() for line in pk.splitlines()]
        firebase_config["private_key"] = "\n".join(lines)
        cred = credentials.Certificate(firebase_config)
    except Exception as e:
        st.error(f"Firebase 인증 실패: {e}")
        st.stop()
    firebase_admin.initialize_app(cred)

db = firestore.client()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "user" not in st.session_state:
    st.error("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user
uid = user["sub"]

def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role":"system","content":"너는 감정을 공감하고 따뜻하게 위로해주는 조력자야."},
            {"role":"user","content":prompt}
        ]
    )
    return response.choices[0].message.content

def save_emotion(uid, text_input, gpt_response, emotion_code="unspecified"):
    db.collection("users").document(uid).collection("emotions").add({
        "input_text": text_input,
        "emotion_code": emotion_code,
        "gpt_response": gpt_response,
        "timestamp": datetime.datetime.now()
    })

comfort_phrases = {
    "joy":"😊 기쁨은 소중한 에너지예요.",
    "sadness":"😢 슬플 땐 충분히 울어도 괜찮아요.",
    "anger":"😠 화가 날 땐 감정을 억누르지 마세요.",
    "anxiety":"😥 불안은 마음의 준비일지도 몰라요.",
    "relief":"😌 나 자신에게 수고했다고 말해주세요.",
    "unspecified":"💭 어떤 감정이든 소중해요. 표현해줘서 고마워요."
}

st.success(f"{user['email']}님, 오늘의 감정을 입력해보세요 ✨")
text_input = st.text_area("당신의 감정을 자유롭게 적어주세요")

if st.button("💌 감정 보내기"):
    if text_input.strip():
        with st.spinner("감정을 공감하고 있어요..."):
            gpt_response = generate_response(text_input)
            save_emotion(uid, text_input, gpt_response)
            st.markdown("#### 💬 GPT의 위로", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background-color:#f0f8ff; padding:15px; border-radius:10px; border:1px solid #dbeafe;'>{gpt_response}<br><br><span style='color:#666;'>💡 {comfort_phrases.get('unspecified')}</span></div>",
                unsafe_allow_html=True
            )
    else:
        st.warning("감정을 입력해주세요.")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("### 📜 내 감정 히스토리")
docs = db.collection("users").document(uid).collection("emotions").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
for doc in docs:
    d = doc.to_dict()
    ts = d['timestamp'].strftime("%Y-%m-%d %H:%M")
    st.markdown(
        f"<div style='border:1px solid #ddd; padding:15px; margin-bottom:15px; border-radius:10px; background:#fff9;'>🗓️ <b>{ts}</b><br><b>📝 감정:</b> {d['input_text']}<br><b>🤖 GPT의 위로:</b> {d['gpt_response']}</div>",
        unsafe_allow_html=True
    )
