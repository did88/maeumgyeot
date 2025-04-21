import streamlit as st
from utils.firebase_utils import get_emotion_history
from utils.font_config import set_korean_font
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# ✅ 한글 폰트 설정
font_prop = set_korean_font()

st.set_page_config(page_title="📜 감정 히스토리", layout="centered")
st.title("📜 내 감정 히스토리")

# ====== 테스트용 세션 설정 (실제 배포 시 제거) ======
if "user" not in st.session_state:
    st.session_state.user = {
        "sub": "test_user_001",
        "email": "tester@example.com"
    }

user = st.session_state.user
uid = user['sub']

# ====== Firestore 동의 여부 확인 ======
from firebase_admin import firestore
db = firestore.client()
user_doc = db.collection("users").document(uid).get()
user_data = user_doc.to_dict() if user_doc.exists else {}

if not user_data.get("agreed_to_terms"):
    st.markdown("## 📄 이용약관 및 개인정보 수집·이용·분석 동의서")
    st.markdown("""
    **제1조 (목적)**  
    본 약관은 사용자가 본 심리 챗봇 서비스를 이용함에 있어 필요한 권리, 의무 및 책임사항을 규정함을 목적으로 하며, 본 서비스는 사용자의 감정, 사고, 행동, 신체상태에 관한 입력값을 바탕으로 GPT API 기반 위로 응답, 감정 태깅, 감정 추이 분석 등 심리 지원 기능을 제공합니다.

    **제2조 (정의)**  
    “서비스”란 사용자 감정 기록 기반 챗봇 인터페이스, 감정분석, 위로 응답, 주간 감정 리포트 제공 등을 포함한 일체의 활동을 의미합니다.  
    “개인정보”란 성명, 이메일, 계정정보, IP주소 등 개인을 식별할 수 있는 정보를 의미합니다.  
    “민감정보”란 감정 상태, 심리적 고충, 정신건강 관련 자기 보고 내용, 꿈 기록, 자기비판 진술 등 심리적 특성을 포함하는 정보를 말합니다.  
    “처리”란 개인정보의 수집, 저장, 조회, 분석, 제공, 삭제 등 일체의 행위를 의미합니다.

    **제3조 ~ 제13조**  
    보안, 보유 기간, 동의 거부 시 영향, 미성년자 제한, GPT 응답의 성격, 열람·정정·삭제 요청 등 자세한 조항이 포함되어 있습니다.

    ✅ **[최종 동의 확인]**  
    □ 본인은 위 약관 및 개인정보 수집·이용·처리·분석에 대한 내용을 충분히 읽고 이해하였으며, 이에 동의합니다.
    """, unsafe_allow_html=True)

    agree = st.checkbox("동의합니다")
    if st.button("확인") and agree:
        db.collection("users").document(uid).update({"agreed_to_terms": True})
        st.experimental_rerun()
    elif not agree:
        st.warning("이용약관에 동의해야 서비스를 이용할 수 있습니다.")
    st.stop()
# ====== 감정 기록 히스토리 로딩 ======
history = get_emotion_history(uid)
if not history:
    st.info("아직 기록된 감정이 없어요. 메인 화면에서 감정을 입력해보세요!")
    st.stop()

# ====== 📈 감정 흐름 시각화 ======
st.subheader("📈 감정 흐름 라인 차트")
df = pd.DataFrame(history)

if "emotion_code" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp")

    emotion_map = {"joy": 2, "relief": 1, "unspecified": 0, "anxiety": -1, "sadness": -2, "anger": -3}
    df["emotion_level"] = df["emotion_code"].map(emotion_map).fillna(0)

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(df["timestamp"], df["emotion_level"], marker='o')
    ax.set_yticks(list(emotion_map.values()))
    ax.set_yticklabels(list(emotion_map.keys()), fontproperties=font_prop)
    ax.set_title("시간에 따른 감정 흐름", fontproperties=font_prop)
    ax.set_xlabel("날짜", fontproperties=font_prop)
    ax.set_ylabel("감정 코드", fontproperties=font_prop)
    plt.xticks(rotation=30, fontproperties=font_prop)
    st.pyplot(fig)
else:
    st.info("아직 감정 코드가 저장된 기록이 없습니다.")

# ====== 감정 카드 리스트 ======
st.markdown("---")
st.markdown("### 🗂 감정 카드 리스트")

for data in reversed(history):
    timestamp = data['timestamp'].strftime('%Y-%m-%d %H:%M') if isinstance(data['timestamp'], datetime.datetime) else str(data['timestamp'])
    st.markdown(f"""
    <div style="border: 1px solid #ddd; padding: 15px 20px; border-radius: 12px; background-color: #ffffffcc; margin-bottom: 20px;">
        <p style="margin:0; color:#888;">🗓️ <b>{timestamp}</b></p>
        <p style="margin:10px 0;"><b>📝 감정:</b><br>{data['input_text']}</p>
        <p style="margin:10px 0;"><b>🤖 GPT의 위로:</b><br>{data['gpt_response']}</p>
        <p style="margin:10px 0;"><b>🏷️ 감정 코드:</b> {data.get('emotion_code', '없음')}</p>
    </div>
    """, unsafe_allow_html=True)
