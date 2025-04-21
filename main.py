import streamlit as st
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
import json

# ====== Streamlit 설정 ======
st.set_page_config(page_title="🫂 마음곁", layout="centered")
st.markdown("""
<h2 style='text-align:center; color:#4a4a4a;'>🫂 마음곁</h2>
<p style='text-align:center; color:#888; font-size: 1.1rem;'>당신의 마음, 곁에 머물다 💛</p>
<hr style='margin-top: 0;'>
""", unsafe_allow_html=True)

# ====== Firebase 초기화 (Cloud secrets용 json.loads 사용) ======
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ====== GPT 클라이언트 초기화 ======
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ====== 로그인 확인 ======
if "user" not in st.session_state:
    st.error("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user
uid = user["sub"]

# ====== GPT 응답 생성 함수 ======
def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 감정을 공감하고 따뜻하게 위로해주는 조력자야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ====== 감정 저장 함수 ======
def save_emotion(uid, text_input, gpt_response, emotion_code="unspecified"):
    doc_ref = db.collection("users").document(uid).collection("emotions").document()
    doc_ref.set({
        "input_text": text_input,
        "emotion_code": emotion_code,
        "gpt_response": gpt_response,
        "timestamp": datetime.datetime.now()
    })

# ====== 위로 문구 모음 ======
comfort_phrases = {
    "joy": "😊 기쁨은 소중한 에너지예요. 오늘도 그 마음 오래 간직하길 바라요.",
    "sadness": "😢 슬플 땐 충분히 울어도 괜찮아요. 당신의 마음을 안아줄게요.",
    "anger": "😠 화가 날 땐 그 감정을 억누르지 말고 천천히 바라보세요.",
    "anxiety": "😥 불안은 미래를 위한 마음의 준비일지도 몰라요. 지금 이 순간을 느껴봐요.",
    "relief": "😌 안도의 순간, 나 자신에게 수고했다고 말해주세요.",
    "unspecified": "💭 어떤 감정이든 소중해요. 표현해줘서 고마워요."
}

# ====== 본문 UI ======
st.success(f"{user['email']}님, 오늘의 감정을 입력해보세요 ✨")
text_input = st.text_area("당신의 감정을 자유롭게 적어주세요")

if st.button("💌 감정 보내기"):
    if text_input.strip():
        with st.spinner("감정을 공감하고 있어요..."):
            gpt_response = generate_response(text_input)
            save_emotion(uid, text_input, gpt_response)

            st.markdown("#### 💬 GPT의 위로")
            st.markdown(f"""
<div style='background-color:#f0f8ff; padding:15px 20px; border-radius:10px; border: 1px solid #dbeafe; color:#222;'>
{gpt_response}<br><br>
<span style='color:#666;'>💡 {comfort_phrases.get('unspecified')}</span>
</div>
""", unsafe_allow_html=True)
    else:
        st.warning("감정을 입력해주세요.")

# ====== 감정 히스토리 출력 ======
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("### 📜 내 감정 히스토리")

docs = db.collection("users").document(uid).collection("emotions")\
    .order_by("timestamp", direction=firestore.Query.DESCENDING).stream()

for doc in docs:
    data = doc.to_dict()
    timestamp = data['timestamp'].strftime('%Y-%m-%d %H:%M') if isinstance(data['timestamp'], datetime.datetime) else str(data['timestamp'])
    st.markdown(f"""
<div style="border: 1px solid #ddd; padding: 15px 20px; border-radius: 12px; background-color: #ffffffcc; margin-bottom: 20px;">
<p style="margin:0; color:#888;">🗓️ <b>{timestamp}</b></p>
<p style="margin:10px 0;"><b>📝 감정:</b><br>{data['input_text']}</p>
<p style="margin:10px 0;"><b>🤖 GPT의 위로:</b><br>{data['gpt_response']}</p>
</div>
""", unsafe_allow_html=True)
