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
    <div style="border:1px solid #ccc; padding:10px; height:300px; overflow-y:scroll;" id="terms_box"
         onscroll="checkScroll()">
        <p><strong>제1조 (목적)</strong><br>
        본 약관은 사용자가 본 심리 챗봇 서비스를 이용함에 있어 필요한 권리, 의무 및 책임사항을 규정함을 목적으로 하며, 본 서비스는 사용자의 감정, 사고, 행동, 신체상태에 관한 입력값을 바탕으로 GPT API 기반 위로 응답, 감정 태깅, 감정 추이 분석 등 심리 지원 기능을 제공합니다.</p>
        <p><strong>제2조 (정의)</strong><br>
        “서비스”란 사용자 감정 기록 기반 챗봇 인터페이스, 감정분석, 위로 응답, 주간 감정 리포트 제공 등을 포함한 일체의 활동을 의미합니다.<br>
        “개인정보”란 성명, 이메일, 계정정보, IP주소 등 개인을 식별할 수 있는 정보를 의미합니다.<br>
        “민감정보”란 감정 상태, 심리적 고충, 정신건강 관련 자기 보고 내용, 꿈 기록, 자기비판 진술 등 심리적 특성을 포함하는 정보를 말합니다.<br>
        “처리”란 개인정보의 수집, 저장, 조회, 분석, 제공, 삭제 등 일체의 행위를 의미합니다.</p>
        <p><strong>제3조 (개인정보 및 민감정보의 수집 항목)</strong><br>
        1. 일반 정보: 이메일 주소, 로그인 정보, Firebase UID, 사용 기기 정보 등<br>
        2. 심리 정보(민감정보): 사용자 입력 감정 및 사고, GPT 기반 분석 결과, 꿈/자기비판 등 자가보고 콘텐츠, 챗봇과의 전체 대화 로그<br>
        3. 기타 정보: 접속 일시, 사용 빈도, 활동 기록 등</p>
        <p><strong>제4조 (수집 및 이용 목적)</strong><br>
        맞춤형 GPT 응답 제공, 감정 변화 시계열 분석, 콘텐츠 및 조언 제공, 서비스 품질 개선, 익명 통계 연구, 관련 법령 준수</p>
        <p><strong>제5조 (정보의 저장 및 보안)</strong><br>
        Firebase 기반 보안환경, Google Cloud 보안 표준, 민감정보 암호화 저장 및 최소 접근, 사용자 요청 시 완전 삭제</p>
        <p><strong>제6조 (정보의 보유 및 이용 기간)</strong><br>
        탈퇴 또는 목적 달성 시까지 보관. 익명화된 데이터는 연구/통계 목적 보유 가능</p>
        <p><strong>제7조 (동의 거부권 및 불이익)</strong><br>
        수집 동의 거부 가능, 단 일부 서비스 제한 가능</p>
        <p><strong>제8조 (타인 정보 입력 금지)</strong><br>
        본인 외 타인 심리정보 입력 및 도용 금지, 법적 책임 있음</p>
        <p><strong>제9조 (GPT API 응답의 성격)</strong><br>
        전문 상담이 아닌 위로 및 자기탐색 도구, 판단 기준 아님</p>
        <p><strong>제10조 (서비스 제공자의 책임 제한)</strong><br>
        사용자의 해석 또는 활용에 따른 피해에 법적 책임 없음. 단, 명백한 과실 시 책임</p>
        <p><strong>제11조 (미성년자 보호)</strong><br>
        만 14세 미만 사용불가, 만 18세 미만은 보호자 동의 필요</p>
        <p><strong>제12조 (동의의 철회 및 열람·정정 요청)</strong><br>
        열람, 수정, 삭제, 수집 거부 등 요청 가능</p>
        <p><strong>제13조 (약관 변경)</strong><br>
        법령 변경 등 사전 고지 후 변경 가능</p>
    </div>
    <p id="scroll_hint" style="color:red;">※ 약관을 끝까지 읽어야 아래 체크박스를 누를 수 있습니다.</p>
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
    """, height=380)
    
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

# ✅ JS 메시지 → Streamlit 전달
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

# ✅ Google 로그인 토큰 처리
params = st.query_params  # 최신 API 사용
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