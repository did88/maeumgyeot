import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt

# 로그인 확인
if "user" not in st.session_state:
    st.warning("로그인이 필요합니다. 좌측 메뉴에서 로그인해주세요.")
    st.stop()

user = st.session_state.user
uid = user["uid"]
email = user["email"]

st.title("📈 내 감정 대시보드")

# Firebase 연결
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 데이터 불러오기
docs = (
    db.collection("users")
    .document(uid)
    .collection("emotions")
    .order_by("timestamp")
    .stream()
)

# 데이터 정리
records = []
for doc in docs:
    d = doc.to_dict()
    ts = d["timestamp"]
    text = d["input_text"]
    codes = d.get("emotion_codes", [])
    gpt = d["gpt_response"]
    date = ts.date() if ts else None
    records.append({
        "날짜": date,
        "감정 텍스트": text,
        "감정 코드": ", ".join(codes),
        "GPT 응답": gpt
    })

if not records:
    st.info("아직 감정 기록이 없습니다.")
    st.stop()

df = pd.DataFrame(records)

# ✅ 5번: 감정 코드 통계
st.subheader("📊 감정 코드 통계")

# 전체 코드 분리 후 집계
from collections import Counter
code_counter = Counter()

for codes in df["감정 코드"]:
    for code in codes.split(", "):
        code_counter[code] += 1

stat_df = pd.DataFrame(code_counter.items(), columns=["감정 코드", "횟수"]).sort_values(by="횟수", ascending=False)

# 막대그래프
fig, ax = plt.subplots()
ax.bar(stat_df["감정 코드"], stat_df["횟수"], color="lightcoral")
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

# 상위 3개 감정 표시
top3 = stat_df.head(3)
st.markdown("#### 💡 자주 느낀 감정 Top 3")
for i, row in top3.iterrows():
    st.markdown(f"- {row['감정 코드']} ({row['횟수']}회)")

st.markdown("---")

# ✅ 6번: GPT 응답 상세 보기
st.subheader("📜 감정 기록 상세 보기")

selected_row = st.selectbox("확인할 날짜 선택", df["날짜"].unique()[::-1])

selected_df = df[df["날짜"] == selected_row]
for _, row in selected_df.iterrows():
    st.markdown(f"#### 📆 {row['날짜']}")
    st.markdown(f"**📝 감정:** {row['감정 텍스트']}")
    st.markdown(f"**🏷️ 감정 코드:** `{row['감정 코드']}`")
    st.markdown(f"**🤖 GPT 위로:**\n> {row['GPT 응답']}")
    st.markdown("---")
