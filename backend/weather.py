# backend/weather.py
import requests
from datetime import datetime

def get_forecast_weather(lat: float, lon: float, days: int = 7):
    """Get max wind speed forecast for next 7 days from Open-Meteo (free, no key)"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wind_speed_10m,wind_gusts_10m",
        "forecast_days": days,
        "timezone": "America/New_York"
    }
    try:
        data = requests.get(url, params=params).json()
        winds = data['hourly']['wind_speed_10m']
        gusts = data['hourly']['wind_gusts_10m']
        return round(max(winds), 1), round(max(gusts), 1)
    except:
        return 12.0, 18.0  # fallback

# Example usage (uncomment to test):
# print(get_forecast_weather(28.56, -80.57))  # Cape Canaveral