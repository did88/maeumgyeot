import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def run(db):
    st.subheader("📈 감정 시계열 분석")
    emotion_data = db.collection_group("emotions").stream()

    rows = []
    for doc in emotion_data:
        d = doc.to_dict()
        if "timestamp" in d and "emotion_codes" in d:
            for code in d["emotion_codes"]:
                rows.append({
                    "date": d["timestamp"].date(),
                    "emotion": code
                })

    if not rows:
        st.info("아직 감정 데이터가 없습니다.")
        return

    df = pd.DataFrame(rows)
    pivot = df.groupby(["date", "emotion"]).size().unstack().fillna(0).sort_index()

    st.line_chart(pivot)
    st.markdown("날짜별 감정 코드 빈도를 시계열로 시각화합니다.")
