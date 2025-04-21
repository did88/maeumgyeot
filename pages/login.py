import streamlit as st
import requests

FIREBASE_API_KEY = st.secrets["firebase_web"]["apiKey"]

st.set_page_config(page_title="🔐 로그인", layout="centered")
st.title("🔐 마음곁 - 로그인")

# ✅ 이미 로그인된 경우 처리
if "user" in st.session_state:
    st.success("이미 로그인되어 있습니다.")
    st.switch_page("main")
    st.stop()

# ✅ 로그인 폼
with st.form("login_form"):
    st.subheader("📥 로그인")
    email = st.text_input("이메일", key="login_email", autocomplete="email")
    password = st.text_input("비밀번호", type="password", key="login_pw", autocomplete="current-password")
    login_submit = st.form_submit_button("로그인")

# ✅ 회원가입 폼
with st.form("signup_form"):
    st.subheader("🆕 회원가입")
    email_signup = st.text_input("이메일", key="signup_email", autocomplete="email")
    password_signup = st.text_input("비밀번호", type="password", key="signup_pw", autocomplete="new-password")
    password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_confirm", autocomplete="new-password")
    agree = st.checkbox("□ 본인은 아래 [이용약관 및 개인정보 수집·이용·분석 동의서]에 동의합니다.", key="terms_agree")

    with st.expander("📜 이용약관 및 개인정보 수집·이용·분석 동의서 보기"):
        st.markdown("""
        (전체 약관 전문 그대로 여기에 들어갑니다.)
        """)
    
    signup_submit = st.form_submit_button("회원가입")

# ✅ 로그인 처리
if login_submit:
    if not email or not password:
        st.warning("이메일과 비밀번호를 입력해주세요.")
    else:
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            res = requests.post(url, json=payload)
            res.raise_for_status()
            user = res.json()
            st.session_state.user = {
                "email": user["email"],
                "uid": user["localId"],
                "idToken": user["idToken"]
            }
            st.success("로그인 성공!")
            st.switch_page("main")
        except requests.exceptions.HTTPError:
            error_msg = res.json().get("error", {}).get("message", "로그인 실패")
            st.error(f"로그인 실패: {error_msg}")

# ✅ 회원가입 처리
if signup_submit:
    if not email_signup or not password_signup or not password_confirm:
        st.warning("모든 항목을 입력해주세요.")
    elif password_signup != password_confirm:
        st.error("비밀번호가 일치하지 않습니다.")
    elif not agree:
        st.error("약관 및 개인정보 수집·이용·분석 동의에 체크해주세요.")
    else:
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
            payload = {
                "email": email_signup,
                "password": password_signup,
                "returnSecureToken": True
            }
            res = requests.post(url, json=payload)
            res.raise_for_status()
            st.success("회원가입 완료! 이제 로그인해주세요.")
        except requests.exceptions.HTTPError:
            error_msg = res.json().get("error", {}).get("message", "회원가입 실패")
            st.error(f"회원가입 실패: {error_msg}")