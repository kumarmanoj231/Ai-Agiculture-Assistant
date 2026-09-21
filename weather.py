import os
from urllib.parse import quote

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_secret(name: str, default=None):
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


API_KEY = get_secret("WEATHER_API_KEY")
BASE_URL = get_secret("WEATHER_BASE_URL", "https://api.weatherapi.com/v1")


def show_weather():
    st.markdown("""
    <style>
    .weather-card {
        background: rgba(255,255,255,0.08);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    city = st.text_input("Enter City", "Guna", key="weather_city")

    if not API_KEY:
        st.warning("Weather service is not configured. Add WEATHER_API_KEY to your Streamlit Secrets.")
        return

    if not city.strip():
        st.info("Enter a city to view the forecast.")
        return

    url = f"{BASE_URL.rstrip('/')}/forecast.json"
    params = {
        "key": API_KEY,
        "q": city.strip(),
        "days": 7,
        "aqi": "yes",
        "alerts": "no",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        st.error(f"Weather API request failed: {exc}")
        return
    except ValueError:
        st.error("Weather API returned an invalid response.")
        return

    location = data.get("location", {})
    current = data.get("current", {})
    forecast_days = data.get("forecast", {}).get("forecastday", [])

    st.write(f"📍 {location.get('name', city)}, {location.get('country', '')}")
    st.metric("Current Temperature", f"{current.get('temp_c', 'N/A')}°C")
    st.caption(current.get("condition", {}).get("text", "Current conditions unavailable"))

    cols = st.columns(min(7, max(1, len(forecast_days))))
    for index, day in enumerate(forecast_days[:7]):
        forecast = day.get("day", {})
        condition = forecast.get("condition", {})
        icon = condition.get("icon", "")
        icon_url = f"https:{icon}" if icon.startswith("//") else icon
        with cols[index % len(cols)]:
            st.markdown(
                f"""
                <div class="weather-card">
                    <div style="font-size:14px;opacity:.7">{day.get('date','')}</div>
                    <img src="{icon_url}" width="60" alt="weather">
                    <div style="font-size:18px">🔺 {forecast.get('maxtemp_c','N/A')}°C</div>
                    <div style="font-size:14px">🔻 {forecast.get('mintemp_c','N/A')}°C</div>
                    <div style="font-size:13px;margin-top:6px">{condition.get('text','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
