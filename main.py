import streamlit as st
import datetime
import re
import emoji
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI, APIError, RateLimitError, Timeout # OpenAI 오류 타입 추가
import json # JSON 파싱을 위해 추가
# utils 폴더의 함수들은 analyze_emotion_and_get_feedback 함수로 통합되므로 주석 처리 또는 삭제
# from utils.gpt_emotion_tagging import get_emotion_codes_combined
# from utils.thinking_trap import detect_thinking_traps

# ✅ 관리자 이메일 (필요 시 사용)
ADMIN_EMAILS = ["wsryang@gmail.com"]

# ✅ 페이지 설정
st.set_page_config(page_title="🫂 마음곁 홈", layout="centered")

# ✅ 로그인 확인
if not st.session_state.get("user"):
    st.markdown("<h1 style='display: flex; align-items: center; gap: 10px;'>🤗 마음곁</h1>", unsafe_allow_html=True)
    st.info("""
    ### 👋 환영합니다!
    **마음곁**은 감정을 기록하고 위로를 받을 수 있는 심리 지원 앱입니다.
    GPT 기반으로 감정을 나누고, 감정 흐름을 돌아보며 자신을 더 이해할 수 있도록 도와드려요.

    🔐 먼저 로그인이 필요합니다.
    👉 **좌측 메뉴에서 로그인** 또는 **회원가입**을 진행해 주세요.
    """)
    st.stop()

# ✅ 로그인된 사용자 정보
user = st.session_state.user
email = user["email"]
uid = user["uid"]

# ✅ Firebase 초기화
# Firebase 앱이 이미 초기화되지 않았는지 확인
if not firebase_admin._apps:
    try:
        # Streamlit secrets에서 Firebase 설정 로드
        firebase_config = dict(st.secrets["firebase"])
        # private_key의 '\n' 문자열을 실제 개행 문자로 변경
        firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
        # 인증서 객체 생성
        cred = credentials.Certificate(firebase_config)
        # Firebase 앱 초기화
        firebase_admin.initialize_app(cred)
    except KeyError:
        st.error("Firebase 설정이 Streamlit secrets에 올바르게 구성되지 않았습니다.")
        st.stop()
    except ValueError as e:
        st.error(f"Firebase 인증서 초기화에 실패했습니다: {e}. 관리자에게 문의해주세요.")
        st.stop()
    except Exception as e:
        st.error(f"Firebase 초기화 중 예상치 못한 오류 발생: {e}")
        st.stop()


# ✅ Firestore 클라이언트 가져오기
try:
    db = firestore.client()
except Exception as e:
    st.error(f"Firestore 클라이언트를 가져오는 데 실패했습니다: {e}")
    st.stop()

# ✅ OpenAI 클라이언트 초기화
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except KeyError:
    st.error("OpenAI API 키가 Streamlit secrets에 설정되지 않았습니다.")
    st.stop()
except Exception as e:
    st.error(f"OpenAI 클라이언트 초기화 실패: {e}")
    st.stop()

# ✅ 위로 문구 딕셔너리
comfort_phrases = {
    "기쁨": "😊 기쁨은 소중한 에너지예요.",
    "슬픔": "😢 슬플 땐 충분히 울어도 괜찮아요.",
    "분노": "😠 화가 날 땐 감정을 억누르지 마세요.",
    "불안": "😥 불안은 마음의 준비일지도 몰라요.",
    "외로움": "😔 외로움을 느끼는 건 당연해요. 함께 있어줄게요.",
    "사랑": "😍 누군가를 사랑한다는 건 참 멋진 일이에요.",
    "무감정/혼란": "😶 혼란스러울 땐 잠시 멈추고 자신을 바라봐요.",
    "지루함": "🥱 지루함도 때론 필요한 감정이에요.",
    "후회/자기비판": "💭 너무 자신을 몰아붙이지 말아요.",
    "unspecified": "💡 어떤 감정이든 소중해요. 표현해줘서 고마워요."
}

# ✅ 유효성 검사 함수
def is_valid_text(text):
    """입력 텍스트의 유효성을 검사합니다."""
    BAD_WORDS = ["씨발", "ㅅㅂ", "ㅂㅅ", "병신", "좆", "꺼져", "fuck", "shit", "asshole", "fucker"]
    text = text.strip()
    # 길이 검사
    if len(text) < 10:
        return False
    # 반복 문자 검사 (예: "ㅋㅋㅋㅋㅋ")
    if re.search(r'(\w)\1{3,}', text):
        return False
    # 동일 단어 반복 검사 (예: "안녕 안녕 안녕")
    words = text.split()
    if len(words) >= 3 and all(w == words[0] for w in words):
        return False
    # 자음/모음만 있는 경우 검사 (예: "ㅋㅎㅋㅎ")
    if all(char in 'ㅋㅎㄷㅠㅏㅣㅜㅔ' for char in text): # 흔한 자음/모음 추가
        return False
    # 이모지만 있는 경우 검사
    if emoji.emoji_count(text) > 0 and len(emoji.replace_emoji(text, replace='')) == 0:
        return False
    # 욕설 검사
    lowered = text.lower()
    if any(bad_word in lowered for bad_word in BAD_WORDS):
        return False
    # 개행 문자를 제외하고 공백만 있는지 검사
    if not re.sub(r'[\n\r]', '', text).strip():
        return False
    return True

# ✅ 통합 GPT 분석 함수 (성능 최적화)
def analyze_emotion_and_get_feedback(text):
    """
    하나의 GPT 호출로 감정 분석, 위로, 코드, 고정관념, 질문 생성.
    JSON 형식으로 결과를 반환합니다.
    """
    # 사용 가능한 감정 및 고정관념 목록 정의 (프롬프트 내에 명시)
    emotion_options = ['기쁨', '슬픔', '분노', '불안', '외로움', '사랑', '무감정/혼란', '지루함', '후회/자기비판', 'unspecified']
    trap_options = ['흑백논리', '과잉일반화', '정신적 여과', '긍정격하', '성급한 결론', '감정적 추론', '해야만 해', '낙인찍기', '개인화', '재앙화']

    prompt = f"""
너는 사용자의 감정 일기를 분석하고 종합적인 피드백을 제공하는 뛰어난 심리 전문가야. 다음 사용자 입력에 대해 아래 항목들을 JSON 형식으로 응답해줘. 모든 텍스트는 한국어로 작성해야 해.

1.  'comfort_response': 사용자의 감정에 깊이 공감하고 따뜻하게 위로하는 메시지 (2-3 문장).
2.  'emotion_codes': 다음 목록 {emotion_options} 중에서 사용자 입력 내용과 가장 관련성이 높은 감정 코드 1~3개를 정확히 골라 리스트 형태로 제공해줘. 관련 감정이 없다면 빈 리스트 []를 반환해.
3.  'thinking_traps': 다음 목록 {trap_options} 중에서 사용자 입력에서 뚜렷하게 감지되는 고정관념(사고의 함정)이 있다면 그 이름을 리스트 형태로 제공해줘. 없다면 빈 리스트 []를 반환해.
4.  'trap_feedback': 위 'thinking_traps'에서 감지된 각 고정관념에 대해, 그것이 어떤 사고방식인지 간략히 설명하고 사용자가 다르게 생각해볼 수 있도록 돕는 구체적인 피드백 메시지를 리스트 형태로 제공해줘. 고정관념이 없다면 빈 리스트 []를 반환해.
5.  'wakeup_question': 만약 'thinking_traps'가 하나 이상 감지되었다면, 사용자가 자신의 생각을 다른 관점에서 성찰해 볼 수 있도록 자극하는, 깊이 있고 열린 형태의 질문 하나를 생성해줘. 고정관념이 없다면 null 값을 반환해.

사용자 입력: "{text}"

JSON 형식의 응답만 제공하고, 다른 설명은 절대 추가하지 마:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # 최신 모델 사용 (또는 gpt-4-turbo 등 비용/성능 고려)
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}, # JSON 출력 모드 강제
            temperature=0.7 # 약간의 창의성을 부여
        )
        content = response.choices[0].message.content

        # GPT 응답이 유효한 JSON인지 파싱 시도
        try:
            result = json.loads(content)

            # 필수 키 존재 여부 및 기본값 설정 (GPT가 형식을 놓칠 경우 대비)
            result.setdefault('comfort_response', "응답 생성에 실패했어요. 다시 시도해주세요.")
            result.setdefault('emotion_codes', [])
            result.setdefault('thinking_traps', [])
            result.setdefault('trap_feedback', [])
            result.setdefault('wakeup_question', None)

            # 감정 코드와 고정관념이 유효한 목록 내에 있는지 확인 (선택적이지만 권장)
            result['emotion_codes'] = [code for code in result.get('emotion_codes', []) if code in emotion_options]
            result['thinking_traps'] = [trap for trap in result.get('thinking_traps', []) if trap in trap_options]

            return result

        except json.JSONDecodeError:
            st.error("죄송합니다, AI 응답을 처리하는 중 오류가 발생했습니다. (JSON 형식 오류)")
            # fallback: 파싱 실패 시 최소한의 정보라도 반환하거나 None 반환
            return {
                'comfort_response': "AI 응답 형식 오류로 인해 위로 메시지를 가져올 수 없습니다.",
                'emotion_codes': [],
                'thinking_traps': [],
                'trap_feedback': [],
                'wakeup_question': None
            }
        except Exception as parse_e:
            st.error(f"죄송합니다, AI 응답 처리 중 예상치 못한 오류 발생: {parse_e}")
            return None


    except APIError as e:
        st.error(f"OpenAI API 오류가 발생했습니다: {e}")
        return None
    except RateLimitError:
        st.error("API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
        return None
    except Timeout:
        st.error("API 요청 시간이 초과되었습니다. 네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요.")
        return None
    except Exception as e:
        st.error(f"감정 분석 중 예상치 못한 오류가 발생했습니다: {e}")
        return None

# ✅ 감정 저장 함수
def save_emotion(uid, text_input, analysis_result):
    """분석된 감정 데이터를 Firestore에 저장합니다."""
    if not analysis_result:
        st.error("분석 결과가 없어 데이터를 저장할 수 없습니다.")
        return False # 저장 실패

    try:
        db.collection("users").document(uid).collection("emotions").add({
            "input_text": text_input,
            "emotion_codes": analysis_result.get("emotion_codes", []),
            "gpt_response": analysis_result.get("comfort_response", ""),
            "thinking_traps": analysis_result.get("thinking_traps", []),
            "trap_feedback": analysis_result.get("trap_feedback", []), # 피드백 저장 추가
            "wakeup_question": analysis_result.get("wakeup_question"), # 마음 깨기 질문 저장
            "timestamp": datetime.datetime.now(datetime.timezone.utc) # UTC 시간으로 저장 권장
        })
        return True # 저장 성공
    except Exception as e:
        st.error(f"데이터 저장 중 오류가 발생했습니다: {e}")
        return False # 저장 실패

# --- Streamlit 앱 UI 구성 ---

st.markdown("### 오늘의 감정을 입력해보세요 ✍️")
text_input = st.text_area("당신의 감정을 자유롭게 적어주세요 (최소 10자 이상)", height=150)

if st.button("💌 감정 보내기"):
    if not is_valid_text(text_input):
        st.warning("⚠️ 감정은 최소 10자 이상, 의미 있는 문장으로 작성해주세요. 반복 단어나 욕설, 또는 자음/모음/이모지만으로는 등록되지 않아요.")
    else:
        # 스피너 표시
        with st.spinner("감정을 분석하고 있어요... 잠시만 기다려주세요 🤔"):
            analysis_result = analyze_emotion_and_get_feedback(text_input)

        # 분석 결과 처리
        if analysis_result:
            # 분석 결과 표시
            gpt_response = analysis_result.get("comfort_response")
            emotion_codes = analysis_result.get("emotion_codes", [])
            thinking_traps = analysis_result.get("thinking_traps", [])
            trap_feedback = analysis_result.get("trap_feedback", [])
            wakeup_question = analysis_result.get("wakeup_question")

            # 고정관념 및 피드백 표시
            if thinking_traps:
                st.markdown("---")
                st.markdown("#### 🧠 감지된 생각의 함정")
                for i, trap in enumerate(thinking_traps):
                    st.markdown(f"- **{trap}**")
                    # 해당 고정관념에 대한 피드백 표시
                    if i < len(trap_feedback):
                         st.markdown(f"<small style='color: #555;'> > {trap_feedback[i]}</small>", unsafe_allow_html=True)
                st.markdown("---") # 구분선

            # 마음 깨기 질문 표시
            if wakeup_question:
                st.markdown("#### 🔍 마음 깨기 질문")
                st.markdown(f"<div style='background-color:#eef; padding:10px; border-radius:8px;'>💡 {wakeup_question}</div>", unsafe_allow_html=True)
                st.markdown("---") # 구분선

            # GPT 위로 및 감정 코드 표시
            st.markdown("#### 💬 AI의 위로와 분석")
            if emotion_codes:
                comfort_lines = [f"💡 {comfort_phrases.get(code, '표현해줘서 고마워요.')}" for code in emotion_codes]
                comfort_hint = "<br>".join(comfort_lines)
            else:
                comfort_hint = comfort_phrases["unspecified"] # 기본 위로 문구

            # 위로 메시지 표시
            st.markdown(
                f"<div style='background-color:#f0f8ff; padding:15px; border-radius:10px; border:1px solid #dbeafe;'>{gpt_response}"
                f"<br><br><span style='color:#666;'>{comfort_hint}</span></div>",
                unsafe_allow_html=True
            )
            # 감정 코드 표시
            if emotion_codes:
                st.markdown(f"🔖 **감정 코드:** `{', '.join(emotion_codes)}`")
            else:
                st.markdown("🔖 **감정 코드:** `분석되지 않음`")

            # 데이터 저장 시도
            if save_emotion(uid, text_input, analysis_result):
                st.success("감정이 성공적으로 기록되었습니다! ✨")
            else:
                st.error("감정 기록 저장에 실패했습니다. 잠시 후 다시 시도해주세요.")

        else:
            # analysis_result가 None인 경우 (analyze_emotion_and_get_feedback 함수 내에서 오류 처리됨)
            st.error("감정 분석 중 문제가 발생하여 결과를 표시할 수 없습니다.")

# ✅ 감정 히스토리 출력
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("### 📜 내 감정 히스토리")

# Firestore에서 최근 N개 기록 가져오기 (성능 최적화)
HISTORY_LIMIT = 20 # 표시할 히스토리 개수 제한
try:
    docs_query = (
        db.collection("users")
        .document(uid)
        .collection("emotions")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(HISTORY_LIMIT)
    )
    docs = docs_query.stream()
    doc_list = list(docs) # stream() 결과를 리스트로 변환하여 사용 (오류 방지 및 재사용 가능)

except Exception as e:
    st.error(f"감정 히스토리를 불러오는 중 오류가 발생했습니다: {e}")
    doc_list = [] # 오류 발생 시 빈 리스트로 초기화

# 히스토리 표시
if not doc_list:
    st.info("아직 기록된 감정이 없어요. 오늘의 감정을 남겨보세요! 😊")
else:
    st.write(f"최근 {len(doc_list)}개의 감정 기록:")
    for doc in doc_list:
        try:
            d = doc.to_dict()

            # 타임스탬프 처리 (타임존 정보 고려)
            ts_obj = d.get("timestamp")
            if ts_obj:
                # Firestore 타임스탬프는 UTC일 수 있으므로 로컬 타임존으로 변환 (선택적)
                # import pytz # 필요시 상단에 import pytz 추가
                # local_tz = pytz.timezone('Asia/Seoul') # 예: 서울 시간
                # local_ts = ts_obj.astimezone(local_tz)
                # ts = local_ts.strftime("%Y-%m-%d %H:%M:%S")
                # 여기서는 기본 형식으로 표시
                ts = ts_obj.strftime("%Y-%m-%d %H:%M")
            else:
                ts = "시간 정보 없음"

            # 데이터 안전하게 가져오기 (키가 없을 경우 대비)
            input_text = d.get('input_text', '내용 없음')
            codes = ", ".join(d.get("emotion_codes", [])) if d.get("emotion_codes") else "분석 안됨"
            traps = ", ".join(d.get("thinking_traps", [])) if d.get("thinking_traps") else "-"
            question = d.get("wakeup_question") if d.get("wakeup_question") else "-"
            gpt_resp = d.get("gpt_response", "내용 없음")

            # 히스토리 항목 표시
            st.markdown(
                f"<div style='border:1px solid #ddd; padding:15px; margin-bottom:15px; border-radius:10px; background:#fff9;'>"
                f"🗓️ <b>{ts}</b><br>"
                f"<b>📝 내가 남긴 글:</b> {st.secrets.get('DEBUG_MODE', False) and input_text or input_text[:100] + '...' if len(input_text) > 100 else input_text }<br>" # 너무 길면 줄이기 (선택적)
                f"<b>🏷️ 감정 코드:</b> {codes}<br>"
                f"<b>🧠 생각의 함정:</b> {traps}<br>"
                f"<b>🧩 마음 깨기 질문:</b> {question}<br>"
                f"<b>🤖 AI의 위로:</b> {gpt_resp[:150] + '...' if len(gpt_resp) > 150 else gpt_resp}" # 너무 길면 줄이기 (선택적)
                f"</div>",
                unsafe_allow_html=True
            )
        except Exception as render_e:
            st.error(f"히스토리 항목을 표시하는 중 오류 발생: {render_e}")
            # 오류가 발생한 항목은 건너뛰거나 간단한 메시지 표시
            st.markdown(f"<div style='border:1px solid #fdd; padding:15px; margin-bottom:15px; border-radius:10px; background:#fff9; color:red;'>오류: 이 기록을 표시할 수 없습니다.</div>", unsafe_allow_html=True)

    # 전체 기록이 더 많을 수 있음을 알림 (선택적)
    # 전체 개수 확인은 추가 쿼리가 필요하므로, 여기서는 간단히 메시지만 표시
    if len(doc_list) == HISTORY_LIMIT:
         st.caption(f"최근 {HISTORY_LIMIT}개의 기록만 표시됩니다.")