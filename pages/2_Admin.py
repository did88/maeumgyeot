import streamlit as st
from firebase_admin import firestore
import pandas as pd
import datetime
import pytz
import matplotlib.pyplot as plt
from utils.font_config import set_korean_font
import io
import xlsxwriter

# 한글 폰트 설정
font_prop = set_korean_font()

st.set_page_config(page_title="📊 관리자 대시보드", layout="wide")
st.title("📊 관리자 대시보드")

# 테스트용 세션 (배포 시 제거)
if "user" not in st.session_state:
    st.session_state.user = {
        "sub": "test_user_001",
        "email": "tester@example.com"
    }

user = st.session_state.user
if user["email"] != "tester@example.com":
    st.error("접근 권한이 없습니다.")
    st.stop()

# Firestore 연결
db = firestore.client()

# ===== 유저 감정 데이터 로드 =====
st.subheader("📈 사용자 감정 기록 분석")
docs = db.collection_group("emotions").stream()

data = []
for doc in docs:
    d = doc.to_dict()
    d["uid"] = doc.reference.parent.parent.id
    data.append(d)

if not data:
    st.info("감정 데이터가 없습니다.")
    st.stop()

df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# ===== 필터 =====
st.sidebar.header("🔍 필터 옵션")
uid_filter = st.sidebar.text_input("UID 검색")
start_date = st.sidebar.date_input("시작 날짜", datetime.date.today() - datetime.timedelta(days=30))
end_date = st.sidebar.date_input("종료 날짜", datetime.date.today())

utc = pytz.UTC
filtered_df = df[
    (df["timestamp"] >= utc.localize(pd.to_datetime(start_date))) &
    (df["timestamp"] <= utc.localize(pd.to_datetime(end_date) + pd.Timedelta(days=1)))
]
if uid_filter:
    filtered_df = filtered_df[filtered_df["uid"].str.contains(uid_filter)]

st.markdown(f"총 {len(filtered_df)}건의 감정 기록이 검색되었습니다.")

# ===== 감정 코드 통계 =====
if "emotion_code" in filtered_df.columns:
    st.subheader("📊 감정 코드 통계")
    emo_counts = filtered_df["emotion_code"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(emo_counts, labels=emo_counts.index, autopct="%1.1f%%", startangle=90, textprops={"fontproperties": font_prop})
    ax.axis("equal")
    st.pyplot(fig)

# ===== CSV 다운로드 =====
st.subheader("⬇️ 감정기록 다운로드")

csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
st.download_button("📁 CSV 다운로드", csv, file_name="filtered_emotions.csv", mime="text/csv")

# ===== Excel 다운로드 =====
if not filtered_df.empty:
    filtered_df["timestamp"] = filtered_df["timestamp"].dt.tz_localize(None)  # 타임존 제거
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="감정기록")

    st.download_button(
        label="📗 Excel 다운로드",
        data=output.getvalue(),
        file_name="filtered_emotions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ===== 감정 카드 리스트 출력 =====
st.markdown("### 📝 감정 카드 리스트")
for _, item in filtered_df.sort_values("timestamp", ascending=False).head(20).iterrows():
    timestamp = item["timestamp"].strftime('%Y-%m-%d %H:%M')
    st.markdown(f"""
    <div style="border:1px solid #444; padding:15px; margin-bottom:12px; border-radius:10px; background-color:#1e1e1e; color:#eee;">
        <b>👤 UID:</b> {item['uid']}<br>
        <b>🕒 시간:</b> {timestamp}<br>
        <b>📝 감정:</b><br> {item['input_text']}<br>
        <b>🤖 GPT:</b><br> {item['gpt_response']}<br>
        <b>🏷️ 코드:</b> {item.get('emotion_code', '없음')}
    </div>
    """, unsafe_allow_html=True)

# ===== 사용자 피드백 보기 =====
st.markdown("---")
st.subheader("📬 사용자 피드백")

feedbacks = db.collection("feedbacks").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()

feedback_data = []
for f in feedbacks:
    d = f.to_dict()
    d["timestamp"] = d["timestamp"].strftime('%Y-%m-%d %H:%M') if isinstance(d["timestamp"], datetime.datetime) else str(d["timestamp"])
    feedback_data.append(d)

if feedback_data:
    feedback_df = pd.DataFrame(feedback_data)
    st.dataframe(feedback_df)

    csv_feedback = feedback_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📁 피드백 CSV 다운로드", csv_feedback, file_name="feedbacks.csv", mime="text/csv")

    output_fb = io.BytesIO()
