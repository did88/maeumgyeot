import streamlit as st
import requests

FIREBASE_API_KEY = st.secrets["firebase_web"]["apiKey"]

st.set_page_config(page_title="🔐 로그인", layout="centered")
st.title("🔐 마음곁 - 로그인")

if "user" in st.session_state:
    st.success("이미 로그인되어 있습니다.")
    st.stop()

# ✅ 자동완성 가능하도록 key 및 autocomplete 추가
email = st.text_input("이메일", key="login_email", autocomplete="email")
password = st.text_input("비밀번호", type="password", key="login_pw", autocomplete="current-password")

if st.button("로그인"):
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
            st.experimental_rerun()
        except requests.exceptions.HTTPError:
            error_msg = res.json().get("error", {}).get("message", "로그인 실패")
            st.error(f"로그인 실패: {error_msg}")

if st.button("회원가입"):
    if not email or not password:
        st.warning("이메일과 비밀번호를 입력해주세요.")
    else:
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            res = requests.post(url, json=payload)
            res.raise_for_status()
            st.success("회원가입 완료! 이제 로그인해주세요.")
        except requests.exceptions.HTTPError:
            error_msg = res.json().get("error", {}).get("message", "회원가입 실패")
            st.error(f"회원가입 실패: {error_msg}")
