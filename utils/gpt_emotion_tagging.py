import openai

# 감정 코드 자동 태깅 함수
def get_emotion_codes(text):
    prompt = f"""
다음 감정 표현을 읽고, 아래의 감정 코드 중 가장 적절한 감정을 추출하세요.

텍스트: "{text}"

가능한 감정 코드 목록:
- 분노
- 슬픔
- 불안
- 외로움
- 사랑
- 기쁨
- 무감정/혼란
- 지루함
- 후회/자기비판

응답 형식:
감정 코드: [감정1, 감정2, ...]

오직 위 목록에 있는 단어만 사용할 것.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 감정 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )

        # 응답에서 감정 코드 추출
        content = response["choices"][0]["message"]["content"]
        # 감정 코드만 리스트로 뽑기
        start = content.find("[")
        end = content.find("]") + 1
        codes = eval(content[start:end])
        return codes

    except Exception as e:
        print(f"[ERROR] GPT 감정 코드 추출 실패: {e}")
        return []
