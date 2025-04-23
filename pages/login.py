import streamlit as st
import requests
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, auth

FIREBASE_API_KEY = st.secrets["firebase_web"]["apiKey"]

# Firebase Admin SDK 초기화
if not firebase_admin._apps:
    cred = credentials.Certificate(st.secrets["firebase"])
    firebase_admin.initialize_app(cred)

st.set_page_config(page_title="🔐 로그인", layout="centered")
st.title("🔐 마음곁 - 로그인")

# ✅ 관리자 메뉴 숨기기 (비로그인 시)
if "user" not in st.session_state:
    st.markdown("""
        <style>
        section[data-testid="stSidebarNav"] ul li a[href*="Admin"],
        section[data-testid="stSidebarNav"] ul li a[href*="admin"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

# ✅ 이미 로그인된 경우
if "user" in st.session_state:
    st.success("이미 로그인되어 있습니다.")
    st.rerun()
    st.stop()

# ✅ 이메일 로그인 폼
with st.form("login_form"):
    st.subheader("📥 이메일 로그인")
    email = st.text_input("이메일", key="login_email", autocomplete="email")
    password = st.text_input("비밀번호", type="password", key="login_pw", autocomplete="current-password")
    login_submit = st.form_submit_button("로그인")

# ✅ 회원가입 폼
with st.form("signup_form"):
    st.subheader("🆕 회원가입")
    email_signup = st.text_input("이메일", key="signup_email", autocomplete="email")
    password_signup = st.text_input("비밀번호", type="password", key="signup_pw", autocomplete="new-password")
    password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_confirm", autocomplete="new-password")

    with st.expander("📜 이용약관 및 개인정보 수집·이용·분석 동의서 보기"):
        components.html("""
        <div style="border:1px solid #ccc; padding:10px; height:200px; overflow-y:scroll;" id="terms_box"
            onscroll="checkScroll()" >
            <p>
            <strong>제1조 (목적)</strong><br> 이 약관은 사용자와 마음곁 간의 권리, 의무, 책임사항을 규정함.<br><br>
            <strong>제2조 (개인정보 수집항목)</strong><br> 이메일, 로그인 기록 등.<br><br>
            <strong>제3조 (수집 목적)</strong><br> 감정 기록 및 통계 제공, 상담 기능 향상 등.<br><br>
            <strong>제13조 (약관 변경)</strong><br>
            - 법령 변경 시 사전 고지 후 변경 가능<br>
            - 변경 사항은 공지 또는 이메일로 고지
            </p>
        </div>
        <p id="scroll_hint" style="color:red;">※ 약관을 끝까지 읽어야 아래 체크박스를 눌러야 합니다.</p>
        <script>
        function checkScroll() {
          var box = document.getElementById("terms_box");
          var hint = document.getElementById("scroll_hint");
          if (box.scrollTop + box.clientHeight >= box.scrollHeight - 5) {
            hint.style.color = 'green';
            hint.innerText = '✅ 약관을 끝까지 읽었습니다. 아래 체크박스를 눌러주세요.';
          }
        }
        </script>
        """, height=300)

    agree = st.checkbox("⬆️ 약관 내용을 모두 읽고 동의합니다.", key="terms_agree_manual")
    signup_submit = st.form_submit_button("회원가입")

# ✅ 이메일 로그인 처리
if login_submit:
    if not email or not password:
        st.warning("이메일과 비밀번호를 입력해주세요.")
    else:
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            payload = {"email": email, "password": password, "returnSecureToken": True}
            res = requests.post(url, json=payload)
            res.raise_for_status()
            user = res.json()
            st.session_state.user = {
                "email": user["email"],
                "uid": user["localId"],
                "idToken": user["idToken"]
            }
            st.success("로그인 성공!")
            st.rerun()
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
        st.error("약관을 끝까지 읽고, 체크박스를 눌러야 가입할 수 있습니다.")
    else:
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
            payload = {"email": email_signup, "password": password_signup, "returnSecureToken": True}
            res = requests.post(url, json=payload)
            res.raise_for_status()
            st.success("회원가입 완료! 이제 로그인해주세요.")
        except requests.exceptions.HTTPError:
            error_msg = res.json().get("error", {}).get("message", "회원가입 실패")
            st.error(f"회원가입 실패: {error_msg}")

# ✅ 구글 로그인 버튼
st.subheader("🔑 또는 Google로 로그인")
components.html(f"""
  <!DOCTYPE html>
  <html>
  <head>
    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <style>
      .g_id_signin {{
        display: flex;
        justify-content: center;
        margin-top: 12px;
      }}
    </style>
  </head>
  <body>
    <div id="g_id_onload"
         data-client_id="{st.secrets['google']['client_id']}"
         data-context="signin"
         data-ux_mode="popup"
         data-callback="handleCredentialResponse"
         data-auto_prompt="false">
    </div>
    <div class="g_id_signin"
         data-type="standard"
         data-size="large"
         data-theme="outline"
         data-text="sign_in_with"
         data-shape="rect"
         data-logo_alignment="left">
    </div>

    <script>
      function handleCredentialResponse(response) {{
        const msg = {{ token: response.credential }};
        window.parent.postMessage(msg, "*");
      }}
    </script>
  </body>
  </html>
""", height=300)

# ✅ 토큰 수신 처리
st.markdown("""
<script>
  window.addEventListener("message", (event) => {
    const data = event.data;
    if (data && data.token) {
      fetch("/?id_token=" + data.token).then(() => window.location.reload());
    }
  }, false);
</script>
""", unsafe_allow_html=True)

params = st.experimental_get_query_params()
if "id_token" in params:
    try:
        decoded = auth.verify_id_token(params["id_token"][0])
        st.session_state.user = {
            "email": decoded["email"],
            "uid": decoded["uid"],
            "idToken": params["id_token"][0]
        }
        st.success("구글 로그인 성공!")
        st.rerun()
    except Exception as e:
        st.error(f"구글 로그인 인증 실패: {e}")
