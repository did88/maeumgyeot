import streamlit as st
import requests

FIREBASE_API_KEY = st.secrets["firebase_web"]["apiKey"]

st.set_page_config(page_title="🔐 로그인", layout="centered")
st.title("🔐 마음곁 - 로그인")

# ✅ 이미 로그인된 경우 처리
if "user" in st.session_state:
    st.success("이미 로그인되어 있습니다.")
    st.rerun()
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
        **제1조 (목적)**  
본 약관은 사용자가 본 심리 챗봇 서비스를 이용함에 있어 필요한 권리, 의무 및 책임사항을 규정함을 목적으로 하며, 본 서비스는 사용자의 감정, 사고, 행동, 신체상태에 관한 입력값을 바탕으로 GPT API 기반 위로 응답, 감정 태깅, 감정 추이 분석 등 심리 지원 기능을 제공합니다.

**제2조 (정의)**  
“서비스”란 사용자 감정 기록 기반 챗봇 인터페이스, 감정분석, 위로 응답, 주간 감정 리포트 제공 등을 포함한 일체의 활동을 의미합니다.  
“개인정보”란 성명, 이메일, 계정정보, IP주소 등 개인을 식별할 수 있는 정보를 의미합니다.  
“민감정보”란 감정 상태, 심리적 고충, 정신건강 관련 자기 보고 내용, 꿈 기록, 자기비판 진술 등 심리적 특성을 포함하는 정보를 말합니다.  
“처리”란 개인정보의 수집, 저장, 조회, 분석, 제공, 삭제 등 일체의 행위를 의미합니다.

**제3조 (개인정보 및 민감정보의 수집 항목)**  
1. 일반 정보: 이메일 주소, 로그인 정보, Firebase UID, 사용 기기 정보 등  
2. 심리 정보 (민감정보): 감정 및 사고 내용, GPT 분석 결과, 꿈, 내면 대화, 자기비판 내용, 챗봇 대화 로그  
3. 기타 정보: 접속 일시, 사용 빈도, 활동 기록 등

**제4조 (수집 및 이용 목적)**  
- 맞춤형 GPT 응답  
- 감정 상태 변화 분석 및 리포트  
- 사용자 맞춤 콘텐츠 제공  
- 서비스 품질 개선 및 알고리즘 학습  
- 익명 통계 데이터 활용  
- 관련 법령 준수

**제5조 (정보의 저장 및 보안)**  
- Firebase 보안환경 기반 저장  
- 민감정보 암호화 저장  
- 삭제 요청 시 즉시 삭제

**제6조 (보유 및 이용 기간)**  
- 회원 탈퇴 또는 목적 달성 시까지 보관  
- 익명화된 데이터는 통계 연구 목적 보관 가능

**제7조 (동의 거부권)**  
- 동의 거부 가능  
- 단, 이 경우 서비스 이용 제한 가능

**제8조 (타인 정보 입력 금지)**  
- 타인의 감정·정보 도용 금지  
- 법적 책임은 사용자 본인에게 있음

**제9조 (GPT API 응답의 성격)**  
- 전문 진단이 아닌 감정적 위로 도구  
- 판단 기준으로 삼아선 안 됨

**제10조 (서비스 제공자의 책임 제한)**  
- 사용자의 입력에 기반한 응답은 책임 제한  
- 보안 사고 발생 시 관련 법령 책임 부담

**제11조 (미성년자 보호)**  
- 만 14세 미만 사용 금지  
- 만 18세 미만은 보호자 동의 책임

**제12조 (동의 철회 및 열람·정정 요청)**  
- 열람, 수정, 삭제, 거부 가능  
- 고객지원 또는 이메일 통해 요청

**제13조 (약관 변경)**  
- 법령 변경 시 사전 고지 후 변경 가능  
- 변경 사항은 공지 또는 이메일로 고지
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
            st.rerun()  # ✅ switch_page("main") 대신 안전하게 재진입
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
