import requests

class OpenMeteoClient:
    def __init__(self, base_url="https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"):
        self.base_url = base_url

    def get_weather_forecast(self, params=None):
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()