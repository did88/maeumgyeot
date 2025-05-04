import streamlit as st
import requests
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials
import json # json 모듈 임포트 확인

# Firebase REST API Key (이메일/비번 로그인, 가입, 비밀번호 재설정에 필요)
try:
    FIREBASE_API_KEY = st.secrets["firebase_web"]["apiKey"]
except KeyError:
    st.error("Firebase Web API 키가 secrets.toml 파일에 설정되지 않았습니다.")
    st.stop()
except Exception as e:
    st.error(f"Firebase Web API 키 로딩 중 오류: {e}")
    st.stop()

# Firebase Admin SDK 초기화 (다른 관리 기능에 필요할 수 있으므로 유지)
if not firebase_admin._apps:
    try:
        firebase_config = dict(st.secrets["firebase"])
        firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    except KeyError:
        st.error("Firebase Admin SDK 설정이 secrets.toml 파일에 올바르게 구성되지 않았습니다.")
        st.stop()
    except Exception as e:
        st.error(f"Firebase Admin SDK 초기화 실패: {e}")
        st.stop()

st.set_page_config(page_title="🔐 로그인", layout="centered")
st.title("🔐 마음곁 - 로그인 / 회원가입")

# ✅ 관리자 메뉴 숨기기 (비로그인 시) - 유지
if "user" not in st.session_state:
    st.markdown("""
        <style>
        section[data-testid="stSidebarNav"] ul li a[href*="Admin"],
        section[data-testid="stSidebarNav"] ul li a[href*="admin"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

# ✅ 이미 로그인된 경우 - 유지
if "user" in st.session_state:
    st.success(f"{st.session_state.user['email']}님, 이미 로그인되어 있습니다.")
    st.page_link("main.py", label="메인 페이지로 이동", icon="🏠")
    st.stop()

# --- 로그인, 회원가입, 비밀번호 재설정 탭 ---
login_tab, signup_tab, reset_pw_tab = st.tabs(["📥 로그인", "🆕 회원가입", "🔑 비밀번호 찾기"])

# ✅ 이메일 로그인 폼 (탭 안으로 이동)
with login_tab:
    with st.form("login_form"):
        st.markdown("##### 이메일로 로그인하세요")
        email = st.text_input("이메일", key="login_email", autocomplete="email")
        password = st.text_input("비밀번호", type="password", key="login_pw", autocomplete="current-password")
        login_submit = st.form_submit_button("로그인")

# ✅ 회원가입 폼 (탭 안으로 이동)
with signup_tab:
    with st.form("signup_form"):
        st.markdown("##### 처음 오셨나요? 가입 후 이용해주세요")
        email_signup = st.text_input("이메일", key="signup_email", autocomplete="email")
        password_signup = st.text_input("비밀번호 (6자 이상)", type="password", key="signup_pw", autocomplete="new-password")
        password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_confirm", autocomplete="new-password")

        with st.expander("📜 이용약관 및 개인정보 수집·이용·분석 동의서 보기"):
            # 약관 내용은 그대로 유지
            components.html("""
            <div style="border:1px solid #ccc; padding:10px; height:200px; overflow-y:scroll; font-size: 0.8em;" id="terms_box"
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
            <p id="scroll_hint" style="color:red; font-size: 0.8em;">※ 약관을 끝까지 스크롤해야 동의 체크박스를 누를 수 있습니다.</p>
            <script>
            function checkScroll() {
              var box = document.getElementById("terms_box");
              var hint = document.getElementById("scroll_hint");
              if (box.scrollTop + box.clientHeight >= box.scrollHeight - 10) {
                hint.style.color = 'green';
                hint.innerText = '✅ 약관 확인 완료! 아래 체크박스를 눌러주세요.';
              } else {
                 hint.style.color = 'red';
                 hint.innerText = '※ 약관을 끝까지 스크롤해야 동의 체크박스를 누를 수 있습니다.';
              }
            }
            document.addEventListener('DOMContentLoaded', function() {
               checkScroll();
            });
            </script>
            """, height=300)

        agree = st.checkbox("위 이용약관 및 개인정보 수집·이용·분석 내용에 모두 동의합니다.", key="terms_agree_manual")
        signup_submit = st.form_submit_button("회원가입")

# --- 🔑 비밀번호 찾기 탭 ---
with reset_pw_tab:
    st.markdown("##### 비밀번호를 잊으셨나요?")
    st.caption("가입 시 사용한 이메일 주소를 입력하시면, 비밀번호를 재설정할 수 있는 링크를 메일로 보내드립니다.")
    with st.form("password_reset_form"):
        reset_email = st.text_input("가입한 이메일 주소", key="reset_email", autocomplete="email")
        reset_submit = st.form_submit_button("비밀번호 재설정 메일 요청")

# --- 폼 제출 처리 로직 ---

# ✅ 이메일 로그인 처리 로직 - 유지 (오류 메시지 약간 수정)
if login_submit:
    if not email or not password:
        st.warning("이메일과 비밀번호를 모두 입력해주세요.")
    else:
        try:
            rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
            response = requests.post(rest_api_url, data=payload, timeout=10)
            response.raise_for_status()

            user_data = response.json()
            st.session_state.user = {
                "email": user_data.get("email"),
                "uid": user_data.get("localId"),
                "idToken": user_data.get("idToken")
            }
            st.success("로그인 성공! 메인 페이지로 이동합니다...")
            st.page_link("main.py", label="메인 페이지로 바로가기", icon="🚀")
            st.stop()

        except requests.exceptions.Timeout:
            st.error("로그인 서버 응답 시간 초과. 잠시 후 다시 시도해주세요.")
        except requests.exceptions.RequestException as e:
            error_msg = "로그인 중 오류 발생"
            try:
                error_data = e.response.json()
                message = error_data.get("error", {}).get("message", "알 수 없는 오류")
                if message in ["INVALID_LOGIN_CREDENTIALS", "INVALID_PASSWORD", "EMAIL_NOT_FOUND", "INVALID_EMAIL"]:
                     error_msg = "이메일 또는 비밀번호가 잘못되었습니다. 다시 확인해주세요."
                else:
                     error_msg = f"오류: {message}"
            except:
                 error_msg = "로그인 서버 연결 실패. 네트워크 상태를 확인해주세요."
            st.error(error_msg)
        except Exception as e:
            st.error(f"로그인 처리 중 예상치 못한 오류 발생: {e}")


# ✅ 회원가입 처리 로직 - 유지
if signup_submit:
    if not email_signup or not password_signup or not password_confirm:
        st.warning("이메일과 비밀번호, 비밀번호 확인을 모두 입력해주세요.")
    elif len(password_signup) < 6:
        st.warning("비밀번호는 6자 이상이어야 합니다.")
    elif password_signup != password_confirm:
        st.error("비밀번호가 일치하지 않습니다.")
    elif not agree:
        st.error("이용약관을 끝까지 읽고 동의 체크박스를 선택해야 가입할 수 있습니다.")
    else:
        try:
            rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
            payload = json.dumps({"email": email_signup, "password": password_signup, "returnSecureToken": True})
            response = requests.post(rest_api_url, data=payload, timeout=10)
            response.raise_for_status()

            st.success("🎉 회원가입이 완료되었습니다! 이제 '로그인' 탭에서 로그인해주세요.")

        except requests.exceptions.Timeout:
            st.error("회원가입 서버 응답 시간 초과. 잠시 후 다시 시도해주세요.")
        except requests.exceptions.RequestException as e:
            error_msg = "회원가입 중 오류 발생"
            try:
                error_data = e.response.json()
                message = error_data.get("error", {}).get("message", "알 수 없는 오류")
                if message == "EMAIL_EXISTS":
                    error_msg = "이미 가입된 이메일 주소입니다. '로그인' 또는 '비밀번호 찾기'를 이용해주세요."
                elif message == "WEAK_PASSWORD : Password should be at least 6 characters":
                    error_msg = "비밀번호가 너무 약합니다. (최소 6자 이상)"
                elif message == "INVALID_EMAIL":
                    error_msg = "유효하지 않은 이메일 형식입니다."
                else:
                    error_msg = f"오류: {message}"
            except:
                error_msg = "회원가입 서버 연결 실패. 네트워크 상태를 확인해주세요."
            st.error(error_msg)
        except Exception as e:
            st.error(f"회원가입 처리 중 예상치 못한 오류 발생: {e}")


# ✅ 비밀번호 재설정 처리 로직 (신규 추가)
if reset_submit:
    if not reset_email:
        st.warning("비밀번호를 재설정할 이메일 주소를 입력해주세요.")
    else:
        try:
            # Firebase Auth REST API 호출 (비밀번호 재설정 메일 발송)
            rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
            # requestType을 "PASSWORD_RESET"으로 지정
            payload = json.dumps({"requestType": "PASSWORD_RESET", "email": reset_email})
            response = requests.post(rest_api_url, data=payload, timeout=10)
            response.raise_for_status()

            # 성공 메시지 표시
            st.success(f"✅ [{reset_email}] 주소로 비밀번호 재설정 안내 메일을 발송했습니다. 메일함을 확인해주세요. (스팸함도 확인해보세요!)")

        except requests.exceptions.Timeout:
            st.error("비밀번호 재설정 요청 서버 응답 시간 초과. 잠시 후 다시 시도해주세요.")
        except requests.exceptions.RequestException as e:
            error_msg = "비밀번호 재설정 요청 중 오류 발생"
            try:
                error_data = e.response.json()
                message = error_data.get("error", {}).get("message", "알 수 없는 오류")
                if message == "EMAIL_NOT_FOUND":
                    error_msg = "입력하신 이메일로 가입된 계정을 찾을 수 없습니다. 이메일 주소를 확인해주세요."
                elif message == "INVALID_EMAIL":
                     error_msg = "유효하지 않은 이메일 형식입니다."
                else:
                    error_msg = f"오류: {message}"
            except:
                error_msg = "서버 연결 실패. 네트워크 상태를 확인해주세요."
            st.error(error_msg)
        except Exception as e:
            st.error(f"비밀번호 재설정 처리 중 예상치 못한 오류 발생: {e}")