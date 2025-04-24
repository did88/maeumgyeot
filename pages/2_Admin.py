import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

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

st.set_page_config(page_title="📊 관리자 전용 페이지", layout="wide")
st.title("📊 관리자 통합 분석 페이지")

# Firebase 연결
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    firebase_config["private_key"] = firebase_config["private_key"].replace("\n", "\n")
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 🔀 탭 선택
tab = st.radio("🔎 보고 싶은 항목을 선택하세요", ["감정 통계", "사용자별 감정 흐름", "사용자 피드백", "고정관념 통계"])

# 사용자 피드백 탭
if tab == "사용자 피드백":
    st.subheader("📬 사용자 피드백 모아보기")
    users = db.collection("users").list_documents()
    for user_doc in users:
        uid = user_doc.id
        feedbacks = (
            db.collection("users")
            .document(uid)
            .collection("feedback")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .stream()
        )
        feedback_list = list(feedbacks)
        if feedback_list:
            st.markdown(f"### 🧑 사용자: `{uid}`")
            for doc in feedback_list:
                data = doc.to_dict()
                timestamp = data.get("timestamp")
                text = data.get("text", "내용 없음")
                st.markdown(f"- 🕒 `{timestamp.strftime('%Y-%m-%d %H:%M')}`<br>✍️ {text}", unsafe_allow_html=True)
            st.markdown("---")
    st.stop()

# 고정관념 통계 탭
if tab == "고정관념 통계":
    st.subheader("🧠 고정관념 및 질문 통계 대시보드")

    trap_counter = Counter()
    daily_traps = defaultdict(lambda: defaultdict(int))
    wakeup_questions = []

    users = db.collection("users").stream()
    for user_doc in users:
        uid = user_doc.id
        emotions = db.collection("users").document(uid).collection("emotions").stream()
        for doc in emotions:
            d = doc.to_dict()
            date = d["timestamp"].date()
            for trap in d.get("thinking_traps", []):
                trap_counter[trap] += 1
                daily_traps[date][trap] += 1
            if d.get("wakeup_question"):
                wakeup_questions.append(d["wakeup_question"])

    st.subheader("📌 전체 고정관념 빈도 Top 10")
    if not trap_counter:
        st.info("고정관념 데이터가 없습니다.")
    else:
        df_traps = pd.DataFrame(trap_counter.items(), columns=["고정관념", "빈도수"]).sort_values(by="빈도수", ascending=False)
        st.dataframe(df_traps.head(10), use_container_width=True)

    if daily_traps:
        all_traps = set(trap for day in daily_traps.values() for trap in day)
        df_time = pd.DataFrame([{"날짜": d, **{t: daily.get(t, 0) for t in all_traps}} for d, daily in daily_traps.items()])
        df_time.set_index("날짜", inplace=True)
        df_time = df_time.sort_index().fillna(0)

        st.subheader("📈 고정관념 시계열 변화")
        fig, ax = plt.subplots(figsize=(12, 5))
        df_time.plot(ax=ax, marker="o")
        ax.set_ylabel("빈도수")
        st.pyplot(fig)

    st.subheader("🧩 생성된 마음 깨기 질문 수")
    st.write(f"총 질문 수: {len(wakeup_questions)}")
    if wakeup_questions:
        st.markdown("#### 샘플 질문 5개")
        for q in wakeup_questions[:5]:
            st.markdown(f"> 💡 {q}")

    st.stop()

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

# 📅 사용자별 감정 흐름 시각화
st.subheader("📅 사용자별 감정 흐름 분석")
try:
    user_docs = db.collection("users").list_documents()
    user_ids = [doc.id for doc in user_docs]
    selected_user = st.selectbox("👤 사용자 선택", user_ids)
    all_emotion_codes = ["기쁨", "슬픔", "분노", "불안", "외로움", "사랑", "무감정/혼란", "지루함", "후회/자기비판"]
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
