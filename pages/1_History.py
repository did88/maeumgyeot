import streamlit as st
from utils.firebase_utils import get_emotion_history
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from utils.font_config import set_korean_font

# 한글 폰트 설정
font_prop = set_korean_font()

st.set_page_config(page_title="📜 감정 히스토리", layout="centered")
st.title("📜 내 감정 히스토리")

# ===== 로그인 확인 =====
if "user" not in st.session_state:
    st.error("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user
uid = user["uid"]

# ===== 감정 기록 히스토리 로딩 ======
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
    plt.xticks(rotation=30)
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
