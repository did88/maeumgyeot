import streamlit as st
import pyrebase

# Firebase Web config (secrets.toml에서 가져옴)
firebase_config = st.secrets["firebase_web"]

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

st.markdown("## 🔐 마음곁 - 로그인")

# 이메일/비밀번호 입력 (처음에는 테스트용 계정으로만)
email = st.text_input("이메일")
password = st.text_input("비밀번호", type="password")

if st.button("로그인"):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.session_state.user = {
            "email": user["email"],
            "idToken": user["idToken"],
            "refreshToken": user["refreshToken"],
            "uid": user["localId"]
        }
        st.success("로그인 성공!")
        st.switch_page("main.py")  # 로그인 후 메인으로 이동
    except Exception as e:
        st.error("로그인 실패 😢")
        st.exception(e)

if st.button("회원가입"):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        st.success("회원가입 완료! 이제 로그인해주세요.")
    except Exception as e:
        st.error("회원가입 실패")
        st.exception(e)
