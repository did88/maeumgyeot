import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.font_config import set_korean_font

def run(db):
    set_korean_font()
    st.subheader("🧩 자기비판 분석")

    docs = db.collection_group("emotions").stream()
    data = []

    for doc in docs:
        d = doc.to_dict()
        if "timestamp" in d and "input_text" in d:
            is_critical = d.get("self_criticism", False)
            emotion_codes = d.get("emotion_codes", [])
            data.append({
                "날짜": d["timestamp"].date(),
                "자기비판": is_critical,
                "감정": ", ".join(emotion_codes) if emotion_codes else "unspecified"
            })

    if not data:
        st.info("분석할 데이터가 없습니다.")
        return

    df = pd.DataFrame(data)

    st.subheader("📊 자기비판 여부에 따른 감정 코드 분포")
    emotion_dist = df.groupby(["자기비판", "감정"]).size().unstack().fillna(0)
    st.bar_chart(emotion_dist.T)

    st.subheader("📈 자기비판 발생 시계열")
    df_daily = df[df["자기비판"] == True].groupby("날짜").size()

    if df_daily.empty:
        st.info("자기비판이 포함된 기록이 없습니다.")
    else:
        st.line_chart(df_daily)
