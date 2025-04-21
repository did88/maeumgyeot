# utils/font_config.py

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

def set_korean_font():
    font_path = os.path.join("assets", "fonts", "NanumGothic.ttf")
    if os.path.exists(font_path):
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.rcParams['axes.unicode_minus'] = False
    else:
        print("⚠️ 내장 폰트 파일이 없습니다. 경로를 확인해주세요.")
