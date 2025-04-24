import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter
from itertools import combinations

def run(db):
    st.subheader("💥 복합 감정 조합 분석")

    emotion_data = db.collection_group("emotions").stream()
    combo_counter = Counter()

    for doc in emotion_data:
        d = doc.to_dict()
        codes = d.get("emotion_codes", [])
        if len(codes) >= 2:
            for pair in combinations(sorted(codes), 2):
                combo_counter[pair] += 1

    if not combo_counter:
        st.info("복합 감정 조합 데이터가 충분하지 않습니다.")
        return

    df = pd.DataFrame(combo_counter.items(), columns=["조합", "빈도수"])
    df = df.sort_values("빈도수", ascending=False)

    st.dataframe(df.head(10), use_container_width=True)

    # Heatmap용 매트릭스 생성
    emotion_set = sorted(set(e for pair in combo_counter for e in pair))
    matrix = pd.DataFrame(0, index=emotion_set, columns=emotion_set)

    for (e1, e2), count in combo_counter.items():
        matrix.loc[e1, e2] = count
        matrix.loc[e2, e1] = count

    st.subheader("🔥 감정 조합 Heatmap")
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(matrix, annot=True, fmt="d", cmap="YlGnBu", ax=ax)
    st.pyplot(fig)
