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
        print(f"✅ 한글 폰트 적용됨: {font_prop.get_name()}")
        return font_prop  # 그래프에 직접 넘겨줄 수 있도록 반환
    else:
        print("❌ NanumGothic.ttf 경로가 잘못되었거나 존재하지 않습니다.")
        return None
