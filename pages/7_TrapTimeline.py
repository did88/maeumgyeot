import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# ✅ Firebase 초기화
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ✅ 로그인 확인
if "user" not in st.session_state:
    st.error("로그인 후 이용해 주세요.")
    st.stop()

uid = st.session_state.user["uid"]

st.set_page_config(page_title="📈 고정관념 변화 추이", layout="centered")
st.title("📈 고정관념별 변화 추이")
st.markdown("시간에 따라 당신의 사고 패턴이 어떻게 변해왔는지 확인해보세요.")

# ✅ 데이터 수집
raw = defaultdict(lambda: defaultdict(int))
docs = db.collection("users").document(uid).collection("emotions").order_by("timestamp").stream()

for doc in docs:
    d = doc.to_dict()
    date = d["timestamp"].date()
    for trap in d.get("thinking_traps", []):
        raw[date][trap] += 1

if not raw:
    st.info("아직 고정관념 기록이 없습니다.")
else:
    # ✅ DataFrame 변환
    all_traps = set(trap for daily in raw.values() for trap in daily)
    df = pd.DataFrame([{"날짜": date, **{t: daily.get(t, 0) for t in all_traps}} for date, daily in raw.items()])
    df.set_index("날짜", inplace=True)
    df = df.sort_index().fillna(0)

    # ✅ 시각화
    st.subheader("🧠 시계열 고정관념 추이")
    fig, ax = plt.subplots(figsize=(12, 5))
    df.plot(ax=ax, marker="o")
    ax.set_title("고정관념 발생 빈도 (날짜별)")
    ax.set_ylabel("빈도수")
    st.pyplot(fig)

    st.subheader("📋 원본 테이블")
    st.dataframe(df, use_container_width=True)
