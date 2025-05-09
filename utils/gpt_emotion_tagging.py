
from openai import OpenAI
import streamlit as st
import ast

VALID_CODES = ["분노", "슬픔", "불안", "외로움", "사랑", "기쁨", "지루함", "후회/자기비판"]

EMOTION_LEXICON_EXTENDED = {
    "분노": ["화나", "짜증", "열받", "미치겠", "빡쳐", "성질", "분노", "환장", "짜증나", "울컥", "짜증남",
             "죽여버리고", "도저히 못 참겠", "개빡쳐", "돌겠다", "부들부들", "손이 부들", "때려치우고 싶어"],
    "슬픔": ["슬퍼", "눈물", "상실", "비참", "우울", "속상", "서럽", "마음 아파", "찢어질", "무너져",
             "허탈", "견딜 수 없어", "이별", "그리움", "상처받", "자괴감"],
    "불안": ["불안", "긴장", "떨려", "무서워", "공포", "초조", "불편해", "불안정", "혼란스러워", "겁나",
             "두려워", "패닉", "심장이 벌렁", "불길", "안절부절", "식은땀"],
    "외로움": ["외로", "혼자", "고독", "적적", "그리워", "허전", "텅빈", "의지할 데 없", "사람이 그리워",
              "연락 없", "마음 붙일 곳", "쓸쓸", "기댈 사람", "혼밥", "혼술"],
    "사랑": ["사랑", "좋아해", "설레", "보고싶", "애틋", "연인", "이뻐", "잘생겼", "사랑스러워",
             "두근", "썸", "짝사랑", "애정", "고마워", "같이 있고 싶어", "끌려"],
    "기쁨": ["기뻐", "행복", "즐거워", "신나", "웃겨", "좋아", "재밌어", "기대돼", "행복감", "감동이야",
             "뿌듯", "힐링", "소름", "짱이야", "대박", "미쳤다", "살맛나"],
    "지루함": ["지루", "심심", "따분", "흥미없", "노잼", "할 게 없어", "하품", "시큰둥", "의욕 없",
               "시간 안 가", "멍함", "답답해", "망할 루틴", "무기력"],
    "후회/자기비판": ["후회", "자책", "내탓", "실수", "바보같", "창피", "민망", "못났어", "왜 그랬을까",
                    "내가 문제야", "부끄러워", "쓸모없", "소심", "자존감 떨어져", "무가치", "망했어"]
}

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def lexicon_based_emotion(text):
    st.text(f"[DEBUG] 사전 감정 키워드 분석 중: {text}")
    for emotion, keywords in EMOTION_LEXICON_EXTENDED.items():
        if any(keyword in text for keyword in keywords):
            st.text(f"[HIT] 감정 '{emotion}' 키워드 감지됨")
            return [emotion]
    st.text("[MISS] 사전 키워드에서 감정 감지 실패")
    return []

def get_emotion_codes(text):
    prompt = f"""
다음 감정 표현을 읽고, 아래 감정 코드 중 가장 적절한 감정을 하나 이상 추론하세요.

텍스트: "{text}"

가능한 감정 코드:
["분노", "슬픔", "불안", "외로움", "사랑", "기쁨", "지루함", "후회/자기비판"]

❗ 응답 형식은 반드시 아래와 같은 JSON 스타일의 문자열 리스트로만 작성하세요:
감정 코드: ["분노"] 또는 감정 코드: ["분노", "외로움"]
※ 감정 단어는 반드시 위 목록에 있는 것 중 하나여야 하며, 임의의 감정 이름은 사용하지 마세요.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 감정 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        content = response.choices[0].message.content
        st.subheader("📄 GPT 응답 원문 (디버그)")
        st.code(content, language="text")

        start = content.find("[")
        end = content.find("]") + 1

        try:
            if start != -1 and end != -1:
                codes = ast.literal_eval(content[start:end])
                codes = [code for code in codes if code in VALID_CODES]  # ✅ 유효 감정만 필터링
                st.text(f"[파싱된 감정 코드] {codes}")
                if codes:
                    return codes
        except Exception as e:
            st.text(f"[literal_eval 파싱 실패] {e}")

    except Exception as e:
        st.text(f"[GPT 요청 실패] {e}")

    st.text("[FALLBACK] 감정 분석 실패 → unspecified 반환")
    return ["unspecified"]

def get_emotion_codes_combined(text):
    lexicon_result = lexicon_based_emotion(text)
    if lexicon_result:
        return lexicon_result
    return get_emotion_codes(text)
