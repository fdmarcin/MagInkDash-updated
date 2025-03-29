"""
This is where we retrieve weather forecast from OpenWeatherMap. Before doing so, make sure you have both the
signed up for an OWM account and also obtained a valid API key that is specified in the config.json file.
"""

import logging
import requests
import json
import string
import datetime


class OWMModule:
    def __init__(self):
        self.logger = logging.getLogger('maginkdash')

    def get_owm_weather(self, lat, lon, api_key):
        # The 3.0 OneCall API requires lat, lon, API key, and we're excluding minutely and alerts data
        url = "https://api.openweathermap.org/data/3.0/onecall?lat=%s&lon=%s&appid=%s&exclude=minutely,alerts&units=metric" % (
            lat, lon, api_key)

        self.logger.info(f"Retrieving weather data from OpenWeatherMap API: {url}")
        response = requests.get(url)

        if response.status_code != 200:
            self.logger.error(f"Error retrieving weather data: {response.status_code} {response.text}")
            # Return empty objects if there's an error
            return {}, [], []

        data = json.loads(response.text)

        # Extract the relevant weather data from the API response
        curr_weather = data.get("current", {})
        hourly_forecast = data.get("hourly", [])
        daily_forecast = data.get("daily", [])

        self.logger.info("Successfully retrieved weather data from OpenWeatherMap")
        return curr_weather, hourly_forecast, daily_forecast

    def get_weather(self, lat, lon, owm_api_key):
        current_weather, hourly_forecast, daily_forecast = self.get_owm_weather(lat, lon, owm_api_key)

        # Log some basic info about the retrieved weather data
        if current_weather and "weather" in current_weather and len(current_weather["weather"]) > 0:
            self.logger.info("Current weather is %s, and the temperature is %s°C." % (
                string.capwords(current_weather["weather"][0]["description"]),
                current_weather.get("temp", "N/A")))

            # Log info about the first hourly forecast
            if hourly_forecast and len(hourly_forecast) > 1:
                next_hour = hourly_forecast[1]
                dt_obj = datetime.datetime.fromtimestamp(next_hour["dt"])
                self.logger.info("Next hour forecast (%s): %s, %.1f°C, Rain: %.0f%%" % (
                    dt_obj.strftime("%H:%M"),
                    string.capwords(next_hour["weather"][0]["description"]),
                    next_hour.get("temp", 0),
                    next_hour.get("pop", 0) * 100))

            # Log info about the daily forecasts
            if daily_forecast and len(daily_forecast) > 0:
                for i in range(min(3, len(daily_forecast))):
                    day = daily_forecast[i]
                    dt_obj = datetime.datetime.fromtimestamp(day["dt"])
                    self.logger.info("Forecast for %s: %s, %.1f-%.1f°C, Rain: %.0f%%" % (
                        dt_obj.strftime("%a, %b %d"),
                        string.capwords(day["weather"][0]["description"]),
                        day["temp"].get("min", 0),
                        day["temp"].get("max", 0),
                        day.get("pop", 0) * 100))
        else:
            self.logger.warning("Weather data is incomplete or not available")

        return current_weather, hourly_forecast, daily_forecast