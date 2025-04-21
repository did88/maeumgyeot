import streamlit as st

# 관리자 이메일 리스트
ADMIN_EMAILS = ["wsryang@gmail.com"]

st.set_page_config(page_title="🫂 마음곁 홈", layout="centered")
st.title("🫂 마음곁")

# 로그인 확인
if "user" not in st.session_state:
    st.warning("로그인이 필요합니다. 좌측 메뉴에서 로그인해주세요.")
    st.stop()

user = st.session_state.user
email = user["email"]

# 사이드바 사용자 표시
st.sidebar.success(f"환영합니다, {email}님")

# 일반 사용자 메뉴
st.sidebar.page_link("pages/1_Emotion_Log.py", label="💌 감정 입력")
st.sidebar.page_link("pages/3_Feedback.py", label="💬 피드백")
st.sidebar.page_link("pages/4_Dream_Analysis.py", label="🌙 꿈 해석")
st.sidebar.page_link("pages/5_SelfCritic_Detector.py", label="🪞 자기비판")

# 관리자 메뉴
if email in ADMIN_EMAILS:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔒 관리자 메뉴**")
    st.sidebar.page_link("pages/2_Admin.py", label="📊 감정 통계")
    st.sidebar.page_link("pages/2_Admin_AllData.py", label="📋 전체 활동 기록")

# 로그아웃
if st.sidebar.button("🚪 로그아웃"):
    del st.session_state.user
    st.rerun()

# 본문 안내
st.markdown("### 마음곁에 오신 걸 환영합니다 💛")
st.markdown("GPT 기반 감정 위로 챗봇으로, 감정 기록과 자기이해를 함께해요.")
st.markdown("좌측 메뉴에서 원하는 기능을 선택해보세요!")
