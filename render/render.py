"""
This script essentially generates a HTML file of the calendar I wish to display. It then fires up a headless Chrome
instance, sized to the resolution of the eInk display and takes a screenshot.

This might sound like a convoluted way to generate the calendar, but I'm doing so mainly because (i) it's easier to
format the calendar exactly the way I want it using HTML/CSS, and (ii) I can delink the generation of the
calendar and refreshing of the eInk display.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from datetime import timedelta
import pathlib
import string
from PIL import Image
import logging
from selenium.webdriver.common.by import By


class RenderHelper:

    def __init__(self, width, height, angle, timeFormat=12):
        self.logger = logging.getLogger('maginkdash')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.htmlFile = 'file://' + self.currPath + '/dashboard.html'
        self.imageWidth = width
        self.imageHeight = height
        self.rotateAngle = angle
        self.timeFormat = timeFormat  # 12 or 24-hour time format

    def set_viewport_size(self, driver):

        # Extract the current window size from the driver
        current_window_size = driver.get_window_size()

        # Extract the client window size from the html tag
        html = driver.find_element(By.TAG_NAME,'html')
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width = self.imageWidth + (current_window_size["width"] - inner_width)
        target_height = self.imageHeight + (current_window_size["height"] - inner_height)

        driver.set_window_rect(
            width=target_width,
            height=target_height)

    def get_screenshot(self, path_to_server_image):
        import subprocess
        import os
        from selenium.webdriver.chrome.service import Service

        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument('--force-device-scale-factor=1')

        # Try to automatically locate chromedriver
        try:
            chromedriver_path = subprocess.check_output(['which', 'chromedriver']).decode('utf-8').strip()
            self.logger.info(f"Found chromedriver at: {chromedriver_path}")
        except (subprocess.SubprocessError, FileNotFoundError):
            # Default paths to try if 'which' command fails
            possible_paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver',
                '/usr/lib/chromium-browser/chromedriver'
            ]

            chromedriver_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chromedriver_path = path
                    self.logger.info(f"Found chromedriver at default location: {chromedriver_path}")
                    break

            if not chromedriver_path:
                self.logger.error("Could not find chromedriver. Please install it with 'sudo apt-get install chromium-chromedriver'")
                raise FileNotFoundError("chromedriver executable not found in PATH")

        # Use the discovered chromedriver path
        service = Service(chromedriver_path)

        try:
            driver = webdriver.Chrome(service=service, options=opts)
            self.set_viewport_size(driver)
            driver.get(self.htmlFile)
            sleep(1)
            driver.get_screenshot_as_file(self.currPath + '/dashboard.png')
            driver.get_screenshot_as_file(path_to_server_image)
            driver.quit()  # Make sure to quit the driver to free resources
            self.logger.info('Screenshot captured and saved to file.')
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            raise

    def get_short_time(self, datetimeObj):
        is24hour = (self.timeFormat == 24)
        datetime_str = ''

        if is24hour:
            # 24-hour format
            datetime_str = '{:02d}:{:02d}'.format(datetimeObj.hour, datetimeObj.minute)
        else:
            # 12-hour format
            if datetimeObj.minute > 0:
                datetime_str = '.{:02d}'.format(datetimeObj.minute)

            if datetimeObj.hour == 0:
                datetime_str = '12{}am'.format(datetime_str)
            elif datetimeObj.hour == 12:
                datetime_str = '12{}pm'.format(datetime_str)
            elif datetimeObj.hour > 12:
                datetime_str = '{}{}pm'.format(str(datetimeObj.hour % 12), datetime_str)
            else:
                datetime_str = '{}{}am'.format(str(datetimeObj.hour), datetime_str)

        return datetime_str

    def process_inputs(
        self,
        current_date,
        current_weather,
        hourly_forecast,
        daily_forecast,
        event_list,
        num_cal_days,
        topic,
        path_to_server_image,
    ):

        # Read html template
        with open(self.currPath + '/dashboard_template.html', 'r') as file:
            dashboard_template = file.read()

        # Populate the date and events
        cal_events_list = []
        for i in range(num_cal_days):
            if len(event_list[i]) > 0:
                cal_events_text = ""
            else:
                cal_events_text = '<div class="event"><span class="event-time">None</span></div>'
            for event in event_list[i]:
                cal_events_text += '<div class="event">'
                if event["isMultiday"] or event["allday"]:
                    cal_events_text += event['summary']
                else:
                    cal_events_text += '<span class="event-time">' + self.get_short_time(event['startDatetime']) + '</span> ' + event['summary']
                cal_events_text += '</div>\n'
            cal_events_list.append(cal_events_text)

        # Default values for weather in case data is missing
        default_weather = {
            "weather": [{"description": "Unknown", "id": 800}],
            "temp": 0
        }
        default_daily = {
            "weather": [{"id": 800}],
            "pop": 0,
            "temp": {"min": 0, "max": 0}
        }

        # Ensure we have valid weather data or use defaults
        if not current_weather or "weather" not in current_weather or len(current_weather["weather"]) == 0:
            self.logger.warning("Current weather data is missing or invalid, using defaults")
            current_weather = default_weather

        next_hour_weather = default_weather
        if hourly_forecast and len(hourly_forecast) > 1:
            next_hour_weather = hourly_forecast[1]

        # Ensure we have valid daily forecast data
        daily_forecast_data = []
        for i in range(min(3, len(daily_forecast))):
            if daily_forecast and len(daily_forecast) > i:
                daily_forecast_data.append(daily_forecast[i])
            else:
                self.logger.warning(f"Daily forecast for day {i} is missing, using defaults")
                daily_forecast_data.append(default_daily)

        # If we have fewer than 3 days, fill in with defaults
        while len(daily_forecast_data) < 3:
            daily_forecast_data.append(default_daily)

        # Determine layout properties based on number of days
        if num_cal_days == 1:
            # Only Today is shown (full width)
            col_today_width = 12
            col_tomorrow_width = 6  # Won't be displayed

            # Set visibility classes
            tomorrow_vis_class = "hidden"
            dayafter_vis_class = "hidden"
        elif num_cal_days == 2:
            # Today and Tomorrow are shown (half width each)
            col_today_width = 6
            col_tomorrow_width = 6

            # Set visibility classes
            tomorrow_vis_class = ""
            dayafter_vis_class = "hidden"
        else:
            # All three days are shown (one-third width each)
            col_today_width = 4
            col_tomorrow_width = 4

            # Set visibility classes
            tomorrow_vis_class = ""
            dayafter_vis_class = ""

        # Build the params dictionary for template formatting
        params = {
            "day": current_date.strftime("%-d"),
            "month": current_date.strftime("%B"),
            "weekday": current_date.strftime("%A"),
            "current_weather_text": string.capwords(next_hour_weather["weather"][0]["description"]),
            "current_weather_id": next_hour_weather["weather"][0]["id"],
            "current_weather_temp": round(next_hour_weather.get("temp", 0)),
            "today_weather_id": daily_forecast_data[0]["weather"][0]["id"],
            "today_weather_pop": str(round(daily_forecast_data[0].get("pop", 0) * 100)),
            "today_weather_min": str(round(daily_forecast_data[0]["temp"].get("min", 0))),
            "today_weather_max": str(round(daily_forecast_data[0]["temp"].get("max", 0))),
            "events_today": cal_events_list[0],
            "col_today_width": col_today_width,
            "tomorrow_vis_class": tomorrow_vis_class,
            "dayafter_vis_class": dayafter_vis_class,
            "topic_title": topic["title"],
            "topic_text": topic["text"],
        }

        # Add day 2 params
        if num_cal_days >= 2:
            params.update({
                "tomorrow": (current_date + timedelta(days=1)).strftime("%A"),
                "events_tomorrow": cal_events_list[1],
                "tomorrow_weather_id": daily_forecast_data[1]["weather"][0]["id"],
                "tomorrow_weather_pop": str(round(daily_forecast_data[1].get("pop", 0) * 100)),
                "tomorrow_weather_min": str(round(daily_forecast_data[1]["temp"].get("min", 0))),
                "tomorrow_weather_max": str(round(daily_forecast_data[1]["temp"].get("max", 0))),
                "col_tomorrow_width": col_tomorrow_width
            })
        else:
            # Default values for tomorrow
            params.update({
                "tomorrow": "",
                "events_tomorrow": "",
                "tomorrow_weather_id": 800,  # Clear sky as default
                "tomorrow_weather_pop": "0",
                "tomorrow_weather_min": "0",
                "tomorrow_weather_max": "0",
                "col_tomorrow_width": col_tomorrow_width
            })

        # Add day 3 params
        if num_cal_days >= 3:
            params.update({
                "dayafter": (current_date + timedelta(days=2)).strftime("%A"),
                "events_dayafter": cal_events_list[2],
                "dayafter_weather_id": daily_forecast_data[2]["weather"][0]["id"],
                "dayafter_weather_pop": str(round(daily_forecast_data[2].get("pop", 0) * 100)),
                "dayafter_weather_min": str(round(daily_forecast_data[2]["temp"].get("min", 0))),
                "dayafter_weather_max": str(round(daily_forecast_data[2]["temp"].get("max", 0)))
            })
        else:
            # Default values for day after tomorrow
            params.update({
                "dayafter": "",
                "events_dayafter": "",
                "dayafter_weather_id": 800,  # Clear sky as default
                "dayafter_weather_pop": "0",
                "dayafter_weather_min": "0",
                "dayafter_weather_max": "0"
            })

        # Write out the HTML file
        htmlFile = open(self.currPath + '/dashboard.html', "w")
        htmlFile.write(dashboard_template.format(**params))
        htmlFile.close()

        # Take the screenshot
        self.get_screenshot(path_to_server_image)