import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt

# 관리자 이메일 목록
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

# Firebase 연결
if not firebase_admin._apps:
    try:
        firebase_config = dict(st.secrets["firebase"])
        firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase 인증 실패: {e}")
        st.stop()

db = firestore.client()

# 📋 모든 사용자 감정 기록
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

# 📊 감정 코드 통계 시각화
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

        # Bar Chart
        st.subheader("📊 감정 코드 막대 그래프")
        fig, ax = plt.subplots()
        ax.bar(df["감정코드"], df["횟수"], color="skyblue")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

        # Pie Chart
        st.subheader("🥧 감정 코드 파이 차트")
        fig2, ax2 = plt.subplots()
        ax2.pie(df["횟수"], labels=df["감정코드"], autopct="%1.1f%%", startangle=140)
        ax2.axis("equal")
        st.pyplot(fig2)

        # CSV 다운로드
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 통계 CSV 다운로드", data=csv, file_name="emotion_code_stats.csv", mime="text/csv")

except Exception as e:
    st.error(f"감정 통계 처리 중 오류 발생: {e}")
