import streamlit as st

st.set_page_config(page_title="🫂 마음곁 홈", layout="centered")
st.title("🫂 마음곁")

# 로그인 확인
if "user" not in st.session_state:
    st.warning("로그인이 필요합니다. 좌측 메뉴에서 로그인해주세요.")
    st.stop()

email = st.session_state.user["email"]
st.sidebar.success(f"환영합니다, {email}님")

# 기본 안내
st.markdown("### 마음곁에 오신 걸 환영합니다 💛")
st.markdown("GPT 기반 감정 위로 챗봇으로, 감정 기록과 자기이해를 함께해요.")
st.markdown("좌측 메뉴에서 원하는 기능을 선택해보세요!")

# 로그아웃 버튼
if st.sidebar.button("🚪 로그아웃"):
    del st.session_state.user
    st.rerun()
