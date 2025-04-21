import streamlit as st
import requests

FIREBASE_API_KEY = st.secrets["firebase_web"]["apiKey"]

st.title("🔐 마음곁 - 로그인")

email = st.text_input("이메일")
password = st.text_input("비밀번호", type="password")

if st.button("로그인"):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        res = requests.post(url, json=payload)
        res.raise_for_status()  # HTTP 에러 시 예외 발생
        user = res.json()
        st.session_state.user = {
            "email": user["email"],
            "uid": user["localId"],
            "idToken": user["idToken"]
        }
        st.success("로그인 성공!")
        st.switch_page("main.py")
    except requests.exceptions.HTTPError as e:
        st.error(f"로그인 실패: {res.json().get('error', {}).get('message', '알 수 없는 오류')}")
    except Exception as e:
        st.error(f"예기치 못한 오류: {e}")

if st.button("회원가입"):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        res = requests.post(url, json=payload)
        res.raise_for_status()
        st.success("회원가입 완료! 이제 로그인 해주세요.")
    except requests.exceptions.HTTPError as e:
        st.error(f"회원가입 실패: {res.json().get('error', {}).get('message', '알 수 없는 오류')}")
