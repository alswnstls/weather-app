import os
import sys
import subprocess

# 패키지 미설치 시 강제 설치 시도 (ModuleNotFoundError 방지)
try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-js-eval"])
    from streamlit_js_eval import get_geolocation

import streamlit as st
import requests
import pandas as pd

# 1. API 키 설정 (보안 규칙 준수)
API_KEY = st.secrets["WEATHER_API_KEY"]
BASE_URL = "http://api.weatherapi.com/v1/forecast.json"

st.set_page_config(page_title="Korea Weather Hub", layout="wide")

# 2. 대한민국 도시 매칭 (기존 기능 유지)
KOREA_CITIES = {
    "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon", "광주": "Gwangju", 
    "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong", "수원": "Suwon", "성남": "Seongnam", 
    "의정부": "Uijeongbu", "안양": "Anyang", "부천": "Bucheon", "광명": "Gyeongmyeong", 
    "평택": "Pyeongtaek", "안산": "Ansan", "고양": "Goyang", "구리": "Guri", "남양주": "Namyangju", 
    "오산": "Osan", "시흥": "Siheung", "군포": "Gunpo", "의왕": "Uiwang", "하남": "Hanam", 
    "용인": "Yongin", "파주": "Paju", "이천": "Icheon", "안성": "Anseong", "김포": "Gimpo", 
    "화성": "Hwaseong", "양주": "Yangju", "포천": "Pocheon", "여주": "Yeoju", "아산": "Asan", 
    "천안": "Cheonan", "충주": "Chungju", "청주": "Cheongju", "전주": "Jeonju", "나주": "Naju", 
    "목포": "Mokpo", "여수": "Yeosu", "포항": "Pohang", "경주": "Gyeongju", "제주": "Jeju", "서귀포": "Seogwipo"
}

def get_weather_data(query):
    search_term = KOREA_CITIES.get(query, query)
    params = {"key": API_KEY, "q": search_term, "days": 7, "aqi": "yes", "lang": "ko"}
    response = requests.get(BASE_URL, params=params)
    return response.json()

# --- UI 레이아웃 및 GPS ---
st.title("🌤️ 스마트 날씨 대시보드")

location = get_geolocation()
city_input = st.text_input("도시 이름을 한글로 입력하세요 (예: 아산, 서울, 제주)", "").strip()

query = None
if city_input:
    query = city_input
elif location:
    lat, lon = location['coords']['latitude'], location['coords']['longitude']
    query = f"{lat},{lon}"

if query:
    data = get_weather_data(query)
    
    if "current" in data:
        curr = data['current']
        loc = data['location']
        cond = curr['condition']['text']
        temp = curr['temp_c']
        pm10 = curr.get('air_quality', {}).get('pm10', 0)

        # 배경 이미지 자동 변경 기능 (복구)
        bg_url = "https://images.unsplash.com/photo-1534088568595-a066f7104211?q=80&w=2000"
        if "맑음" in cond or "Sunny" in cond:
            bg_url = "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=2000"
        elif "비" in cond or "Rain" in cond:
            bg_url = "https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?q=80&w=2000"
        elif "눈" in cond or "Snow" in cond or "진눈깨비" in cond:
            bg_url = "https://images.unsplash.com/photo-1491002052546-bf38f186af56?q=80&w=2000"

        st.markdown(
            f"""
            <style>
            .stApp {{ background-image: url("{bg_url}"); background-size: cover; background-attachment: fixed; }}
            .glass {{ background: rgba(0, 0, 0, 0.7); padding: 25px; border-radius: 15px; color: white; border: 1px solid rgba(255,255,255,0.2); }}
            [data-testid="stMetricValue"] {{ color: white !important; }}
            </style>
            """, unsafe_allow_html=True
        )

        with st.container():
            st.markdown('<div class="glass">', unsafe_allow_html=True)
            st.header(f"📍 {loc['name']} ({loc['country']})")
            
            # 메트릭 섹션 (미세먼지 포함)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("현재 온도", f"{temp}°C")
            c2.metric("날씨 상태", cond)
            c3.metric("습도", f"{curr['humidity']}%")
            c4.metric("바람", f"{curr['wind_kph']} km/h")
            c5.metric("미세먼지", f"{round(pm10, 1)}")

            if temp >= 30: st.error("너무 더워요! 🥵")
            elif temp <= 10: st.warning("조금 쌀쌀해요! 🧣")
            
            st.markdown("---")
            
            # 그래프 섹션 (7일 예보 복구)
            f_days = data['forecast']['forecastday']
            df = pd.DataFrame([{
                "날짜": d["date"][5:],
                "최고기온": d["day"]["maxtemp_c"],
                "최저기온": d["day"]["mintemp_c"],
                "강수확률(%)": d["day"]["daily_chance_of_rain"]
            } for d in f_days]).set_index("날짜")

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.subheader("🌡️ 7일 최고/최저 기온 (°C)")
                st.bar_chart(df[["최고기온", "최저기온"]])
            with col_chart2:
                st.subheader("☔ 날짜별 강수 확률 (%)")
                st.bar_chart(df["강수확률(%)"])
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error(f"'{query}' 지역 정보를 찾을 수 없습니다.")
else:
    st.info("도시를 입력하거나 GPS 위치 권한을 허용해 주세요.")