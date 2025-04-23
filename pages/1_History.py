
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ✅ 폰트 설정 (NanumGothic)
font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "NanumGothic.ttf"))
font_prop = fm.FontProperties(fname=font_path)
fm.fontManager.addfont(font_path)
plt.rc('font', family=font_prop.get_name())
plt.rcParams["axes.unicode_minus"] = False

# ✅ 영어 감정 코드 → 한글 변환 매핑
EMOTION_TRANSLATE = {
    "joy": "기쁨",
    "sadness": "슬픔",
    "anger": "분노",
    "anxiety": "불안",
    "loneliness": "외로움",
    "love": "사랑",
    "neutral": "무감정/혼란",
    "boredom": "지루함",
    "regret": "후회/자기비판",
    "unspecified": None  # 삭제 대상
}

if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.set_page_config(page_title="📜 감정 히스토리", layout="centered")
st.title("📜 내 감정 히스토리")
st.subheader("📈 감정 흐름 라인 차트")

# 현재 로그인한 사용자
if "user" not in st.session_state:
    st.warning("로그인이 필요합니다. 좌측 메뉴에서 로그인해주세요.")
    st.stop()

uid = st.session_state.user["uid"]

# 🔎 사용자 감정 기록 조회
docs = (
    db.collection("users")
    .document(uid)
    .collection("emotions")
    .order_by("timestamp")
    .stream()
)

records = []
for doc in docs:
    d = doc.to_dict()
    timestamp = d["timestamp"]
    date = timestamp.date()
    for code in d.get("emotion_codes", []):
        translated = EMOTION_TRANSLATE.get(code, code)
        if translated:  # unspecified 제외
            records.append({"날짜": date, "감정": translated})

if not records:
    st.info("아직 감정 기록이 없습니다.")
else:
    df = pd.DataFrame(records)
    fig, ax = plt.subplots(figsize=(10, 4))
    df["count"] = 1
    grouped = df.groupby(["날짜", "감정"]).count().reset_index()
    pivot = grouped.pivot(index="날짜", columns="감정", values="count").fillna(0)
    pivot.plot(ax=ax, marker="o")
    ax.set_title("시간에 따른 감정 흐름")
    ax.set_ylabel("감정 빈도")
    st.pyplot(fig)

    st.subheader("📋 감정 기록 테이블")
    st.dataframe(df[::-1], use_container_width=True)
