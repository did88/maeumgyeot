
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ✅ NanumGothic을 matplotlib에 직접 등록하여 깨짐 방지
font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "NanumGothic.ttf"))
font_prop = fm.FontProperties(fname=font_path)
fm.fontManager.addfont(font_path)
plt.rc('font', family=font_prop.get_name())
plt.rcParams["axes.unicode_minus"] = False

ADMIN_EMAILS = ["wsryang@gmail.com"]

def is_admin():
    return (
        "user" in st.session_state
        and st.session_state.user["email"] in ADMIN_EMAILS
    )

if not is_admin():
    st.error("⛔ 접근 권한이 없습니다. 관리자만 접근 가능합니다.")
    st.stop()

st.title("📊 관리자 전용 페이지")

if not firebase_admin._apps:
    try:
        firebase_config = dict(st.secrets["firebase"])
        firebase_config["private_key"] = firebase_config["private_key"].replace("\n", "\n")
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase 인증 실패: {e}")
        st.stop()

db = firestore.client()

st.subheader("📋 모든 감정 기록")

try:
    users_ref = db.collection("users").list_documents()
    for user_doc in users_ref:
        uid = user_doc.id
        emotions = (
            db.collection("users")
            .document(uid)
            .collection("emotions")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(3)
            .stream()
        )
        st.markdown(f"#### 🧑 사용자: {uid}")
        for doc in emotions:
            data = doc.to_dict()
            st.write(f"- 🕒 {data['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            st.write(f"  - 감정: {data['input_text']}")
            st.write(f"  - 감정 코드: {', '.join(data.get('emotion_codes', ['unspecified']))}")
            st.write(f"  - GPT 응답: {data['gpt_response']}")
except Exception as e:
    st.error(f"데이터 불러오기 실패: {e}")

st.markdown("---")

st.subheader("📈 감정 코드 통계 시각화")

try:
    docs = db.collection_group("emotions").stream()

    emotion_counts = {}
    for doc in docs:
        d = doc.to_dict()
        codes = d.get("emotion_codes", [])
        for code in codes:
            emotion_counts[code] = emotion_counts.get(code, 0) + 1

    if not emotion_counts:
        st.info("아직 저장된 감정 코드가 없습니다.")
    else:
        df = pd.DataFrame(list(emotion_counts.items()), columns=["감정코드", "횟수"]).sort_values(by="횟수", ascending=False)

        st.subheader("📊 감정 코드 막대 그래프")
        fig, ax = plt.subplots()
        ax.bar(df["감정코드"], df["횟수"], color="skyblue")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

        st.subheader("🥧 감정 코드 파이 차트")
        fig2, ax2 = plt.subplots()
        ax2.pie(df["횟수"], labels=df["감정코드"], autopct="%1.1f%%", startangle=140)
        ax2.axis("equal")
        st.pyplot(fig2)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 통계 CSV 다운로드", data=csv, file_name="emotion_code_stats.csv", mime="text/csv")

except Exception as e:
    st.error(f"감정 통계 처리 중 오류 발생: {e}")

st.markdown("---")

st.subheader("📅 사용자별 감정 흐름 분석")

try:
    user_docs = db.collection("users").list_documents()
    user_ids = [doc.id for doc in user_docs]

    selected_user = st.selectbox("👤 사용자 선택", user_ids)

    all_emotion_codes = [
        "기쁨", "슬픔", "분노", "불안", "외로움",
        "사랑", "무감정/혼란", "지루함", "후회/자기비판"
    ]
    selected_code = st.selectbox("🏷️ 추적할 감정 코드 선택", all_emotion_codes)

    docs = (
        db.collection("users")
        .document(selected_user)
        .collection("emotions")
        .order_by("timestamp")
        .stream()
    )

    records = []
    for doc in docs:
        d = doc.to_dict()
        timestamp = d["timestamp"]
        date = timestamp.date() if timestamp else None
        if not date:
            continue
        if selected_code in d.get("emotion_codes", []):
            records.append(date)

    if not records:
        st.info(f"{selected_user}의 '{selected_code}' 기록이 없습니다.")
    else:
        df = pd.DataFrame(records, columns=["날짜"])
        freq = df["날짜"].value_counts().sort_index()
        freq_df = freq.reset_index()
        freq_df.columns = ["날짜", "빈도"]
        st.line_chart(freq_df.set_index("날짜"))

except Exception as e:
    st.error(f"감정 흐름 시각화 오류: {e}")
