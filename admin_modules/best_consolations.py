
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from utils.font_config import set_korean_font


import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 직접 한글 폰트 경로 설정
font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "NanumGothic.ttf"))
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False
def run(db):
    set_korean_font()
    st.subheader("🎁 GPT 위로 문구 효과 분석")

    docs = db.collection_group("emotions").stream()
    records = []

    for doc in docs:
        d = doc.to_dict()
        ts = d.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except:
                continue
        if ts and "gpt_response" in d and "emotion_codes" in d:
            text = d.get("gpt_response", "")
            text = text.strip()[:100] if isinstance(text, str) else ""
            records.append({
                "날짜": ts.date(),
                "위로문구": text,
                "감정": ", ".join(d["emotion_codes"]) if d["emotion_codes"] else "unspecified"
            })

    if not records:
        st.info("위로 문구 기록이 없습니다.")
        return

    df = pd.DataFrame(records)

    st.subheader("🏆 가장 많이 쓰인 GPT 위로 문구 Top 5")
    phrase_counts = df["위로문구"].value_counts().head(5)
    st.dataframe(phrase_counts.rename_axis("문구").reset_index(name="횟수"))

    st.subheader("📊 감정 코드별 위로 문구 분포")
    try:
        emotion_phrase_df = df.groupby(["감정", "위로문구"]).size().unstack(fill_value=0)
        st.bar_chart(emotion_phrase_df.T.head(10))
    except:
        st.warning("데이터가 너무 희소하거나 시각화에 부적합한 구조입니다.")

    st.markdown("""
    위로 문구가 특정 감정에서 자주 등장하는지 확인하고,  
    반응이 좋았던 문구를 추출하여 향후 자동 추천 모델에도 활용할 수 있습니다.
    """)
