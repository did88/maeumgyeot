import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
from utils.font_config import set_korean_font

def run(db):
    set_korean_font()
    st.subheader("📉 고정관념 변화 시계열 분석")

    trap_counter = Counter()
    daily_traps = defaultdict(lambda: defaultdict(int))

    emotion_docs = db.collection_group("emotions").stream()

    for doc in emotion_docs:
        d = doc.to_dict()
        if "timestamp" in d and "thinking_traps" in d:
            date = d["timestamp"].date()
            for trap in d["thinking_traps"]:
                trap_counter[trap] += 1
                daily_traps[date][trap] += 1

    if not trap_counter:
        st.info("고정관념 데이터가 없습니다.")
        return

    st.subheader("🔝 고정관념 등장 Top 10")
    df_top = pd.DataFrame(trap_counter.items(), columns=["고정관념", "빈도수"]).sort_values(by="빈도수", ascending=False)
    st.dataframe(df_top.head(10), use_container_width=True)

    st.subheader("📈 고정관념 시계열 변화 추이")
    all_traps = set(trap for daily in daily_traps.values() for trap in daily)
    df_time = pd.DataFrame([
        {"날짜": date, **{t: daily.get(t, 0) for t in all_traps}}
        for date, daily in daily_traps.items()
    ])
    df_time = df_time.sort_values("날짜")
    df_time.set_index("날짜", inplace=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    df_time.plot(ax=ax, marker="o")
    ax.set_ylabel("빈도수")
    ax.set_title("고정관념별 일자별 등장 추이")
    st.pyplot(fig)
