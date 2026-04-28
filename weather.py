import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = os.getenv("WEATHER_BASE_URL")


def show_weather():

    st.markdown("""
    <style>
    .weather-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: 0.3s;
    }

    .weather-card:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: scale(1.03);
    }
    </style>
    """, unsafe_allow_html=True)

    unit = "Celsius"
    city = st.text_input("Enter City", "Guna")
    days = 7

    url = f"{BASE_URL}/forecast.json?key={API_KEY}&q={city}&days={days}&aqi=yes&alerts=no"
    try:
        r = requests.get(url)
        r.raise_for_status()
    except Exception as e:
        st.error("Weather API failed")
        return

    if r.status_code == 200:

        data = r.json()
        loc = data['location']['name']
        country = data['location']['country']

        temp = data['current']['temp_c'] if unit == "Celsius" else data['current']['temp_f']
        cond = data['current']['condition']['text']
        icon = "https:" + data['current']['condition']['icon']

        st.write(f"📍 {loc}, {country}")

        
        forecast_days = data['forecast']['forecastday']

        cols = st.columns(days)

        for i, day in enumerate(forecast_days):

            date = day['date']
            min_temp = day['day']['mintemp_c'] if unit == "Celsius" else day['day']['mintemp_f']
            max_temp = day['day']['maxtemp_c'] if unit == "Celsius" else day['day']['maxtemp_f']
            condition = day['day']['condition']['text']
            icon_url = "https:" + day['day']['condition']['icon']

            with cols[i]:

                st.markdown(f"""
                <div class="weather-card">
                    <div style="font-size:14px; opacity:0.7;">{date}</div>
                    <img src="{icon_url}" width="60">
                    <div style="font-size:18px; margin-top:5px;">
                        🔺 {max_temp}°{unit[0]}
                    </div>
                    <div style="font-size:14px; opacity:0.8;">
                        🔻 {min_temp}°{unit[0]}
                    </div>
                    <div style="font-size:13px; margin-top:6px; opacity:0.6;">
                        {condition}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.error("City not found!")