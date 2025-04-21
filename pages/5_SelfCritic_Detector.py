import streamlit as st
from firebase_admin import firestore
from openai import OpenAI
import datetime

# 페이지 설정
st.set_page_config(page_title="🪞 자기비판 탐지", layout="centered")
st.title("🪞 자기비판 탐지 챗봇")

# 테스트용 세션 (배포 시 제거)
if "user" not in st.session_state:
    st.session_state.user = {
        "sub": "test_user_001",
        "email": "tester@example.com"
    }

user = st.session_state.user
uid = user["sub"]

# OpenAI 클라이언트
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# GPT 프롬프트 함수
def analyze_self_criticism(text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content":
             "너는 심리상담가야. 사용자가 쓴 문장에서 자기비판, 자기혐오, 완벽주의적 사고를 감지하고 "
             "그 안의 '비판자 자아'가 어떤 존재인지 해석해줘. "
             "그 후 사용자가 자신의 내면을 더 깊이 탐색할 수 있도록 후속 질문 2~3개를 제안해줘. "
             "단, 판단하거나 훈계하듯 말하지 말고, 공감적으로 표현해줘."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

# 사용자 입력
st.markdown("자신을 비판하거나 괴롭히는 생각이 들 때, 자유롭게 표현해보세요.")
user_input = st.text_area("📝 최근 스스로에게 들었던 말, 생각, 느낌 등을 적어보세요.", height=200)

if st.button("🔍 분석하기"):
    if user_input.strip():
        with st.spinner("당신의 내면을 살펴보고 있어요..."):
            result = analyze_self_criticism(user_input)

            # Firestore 저장
            db = firestore.client()
            db.collection("users").document(uid).collection("self_critic").add({
                "input_text": user_input,
                "gpt_response": result,
                "timestamp": datetime.datetime.now()
            })

            # 결과 출력
            st.success("내면 분석이 완료되었습니다!")
            st.markdown("#### 💬 GPT의 분석과 탐색 질문")
            st.markdown(f"""
            <div style='background-color:#f0f8ff; padding:15px 20px; border-radius:10px; border: 1px solid #dbeafe; color:#222;'>
                {result}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("문장을 입력해주세요.")
