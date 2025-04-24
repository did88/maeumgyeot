import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

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

# ✅ 고정관념 통계 집계
st.set_page_config(page_title="🧠 고정관념 통계", layout="centered")
st.title("🧠 감정 속 고정관념 통계")
st.markdown("당신의 감정 기록에서 어떤 고정관념이 자주 등장했는지 확인해보세요.")

# Firestore 데이터 가져오기
traps = []
docs = db.collection("users").document(uid).collection("emotions").stream()
for doc in docs:
    d = doc.to_dict()
    traps.extend(d.get("thinking_traps", []))

if not traps:
    st.info("아직 감정 기록에 고정관념이 감지되지 않았어요.")
else:
    counter = Counter(traps)
    df = pd.DataFrame(counter.items(), columns=["고정관념", "빈도수"]).sort_values(by="빈도수", ascending=False)

    # 시각화
    st.subheader("📊 고정관념 빈도 시각화")
    fig, ax = plt.subplots()
    df.set_index("고정관념").plot(kind="bar", ax=ax, legend=False, color="#74b9ff")
    ax.set_ylabel("빈도수")
    ax.set_title("감정 입력에서 자주 나타난 고정관념")
    st.pyplot(fig)

    # 데이터 테이블
    st.subheader("📋 고정관념 목록")
    st.dataframe(df, use_container_width=True)
