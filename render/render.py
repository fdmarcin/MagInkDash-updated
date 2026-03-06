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

    def calculate_optimal_days(self, all_event_list, max_events_per_day=8, max_total_events=20):
        """
        Calculate the optimal number of days to display based on available events
        and estimated space constraints.

        Args:
            all_event_list: List of event lists for each day
            max_events_per_day: Maximum events that fit comfortably in one day
            max_total_events: Maximum total events that fit in the calendar area

        Returns:
            int: Optimal number of days to display (1-7)
        """
        if not all_event_list or len(all_event_list) == 0:
            return 1  # Show at least today even if no events

        total_events = 0
        optimal_days = 1

        for day_index, day_events in enumerate(all_event_list):
            if day_index >= 7:  # Don't go beyond a week
                break

            day_event_count = len(day_events)

            # If this day has no events and we already have some days, consider stopping
            if day_event_count == 0 and day_index >= 2:
                # Only add empty days if we have very few events so far
                if total_events < 5:
                    optimal_days = day_index + 1
                    continue
                else:
                    break

            # If adding this day would exceed our limits, stop
            if (total_events + day_event_count > max_total_events or
                day_event_count > max_events_per_day):
                break

            total_events += day_event_count
            optimal_days = day_index + 1

            # If we have a good amount of events, don't go beyond 3 days
            if total_events >= 12 and optimal_days >= 3:
                break

        # Ensure we show at least today and tomorrow if tomorrow has events
        if optimal_days == 1 and len(all_event_list) > 1 and len(all_event_list[1]) > 0:
            optimal_days = 2

        # Cap at 3 days maximum for layout reasons
        optimal_days = min(optimal_days, 3)

        self.logger.info(f"Calculated optimal days to show: {optimal_days} (total events: {total_events})")

        return optimal_days

    def process_inputs(
        self,
        current_date,
        all_event_list,  # Now receives all events
        path_to_server_image,
        max_events_per_day=8,
        max_total_events=20,
    ):
        # Determine optimal number of days to show based on events
        optimal_days = self.calculate_optimal_days(
            all_event_list,
            max_events_per_day=max_events_per_day,
            max_total_events=max_total_events,
        )

        # Use only the events for the optimal number of days
        event_list = all_event_list[:optimal_days]
        num_cal_days = optimal_days

        # Read html template
        with open(self.currPath + '/dashboard_template.html', 'r') as file:
            dashboard_template = file.read()

        # Populate the date and events
        cal_events_list = []
        for i in range(num_cal_days):
            if len(event_list[i]) > 0:
                cal_events_text = ""
            else:
                cal_events_text = '<div class="event"><span class="event-time">Nothing to do!</span></div>'
            for event in event_list[i]:
                cal_events_text += '<div class="event">'
                if event["isMultiday"] or event["allday"]:
                    cal_events_text += event['summary']
                else:
                    cal_events_text += '<span class="event-time">' + self.get_short_time(event['startDatetime']) + '</span> ' + event['summary']
                cal_events_text += '</div>\n'
            cal_events_list.append(cal_events_text)

        # Determine layout properties based on number of days
        if num_cal_days == 1:
            # Only Today is shown (full width)
            col_tomorrow_width = 6  # Won't be displayed

            # Set visibility classes
            tomorrow_vis_class = "hidden"
            dayafter_vis_class = "hidden"
        elif num_cal_days == 2:
            # Today and Tomorrow are shown (half width each)
            col_tomorrow_width = 6

            # Set visibility classes
            tomorrow_vis_class = ""
            dayafter_vis_class = "hidden"
        else:
            # All three days are shown
            col_tomorrow_width = 4

            # Set visibility classes
            tomorrow_vis_class = ""
            dayafter_vis_class = ""

        total_events_displayed = sum(len(day) for day in event_list)

        day_label_cache = {
            0: "Today",
            1: "Tomorrow",
        }

        def get_day_label(offset):
            if offset in day_label_cache:
                return day_label_cache[offset]
            return (current_date + timedelta(days=offset)).strftime("%A")

        next_event_text = "Next: Nothing scheduled"
        next_event_found = False
        for day_index, events in enumerate(event_list):
            if events:
                first_event = events[0]
                if first_event["isMultiday"] or first_event["allday"]:
                    event_label = first_event['summary']
                else:
                    event_label = f"{self.get_short_time(first_event['startDatetime'])} {first_event['summary']}"
                next_event_text = f"Next: {event_label} ({get_day_label(day_index)})"
                next_event_found = True
                break

        if not next_event_found and total_events_displayed == 0:
            next_event_text = "Next: Enjoy the free time"

        if total_events_displayed == 0:
            day_word = "day" if num_cal_days == 1 else "days"
            calendar_summary = f"No events over the next {num_cal_days} {day_word}"
        else:
            event_word = "event" if total_events_displayed == 1 else "events"
            day_word = "day" if num_cal_days == 1 else "days"
            calendar_summary = f"{total_events_displayed} {event_word} across {num_cal_days} {day_word}"

        # Build the params dictionary for template formatting
        params = {
            "day": current_date.strftime("%-d"),
            "month": current_date.strftime("%B"),
            "weekday": current_date.strftime("%A"),
            "events_today": cal_events_list[0],
            "tomorrow_vis_class": tomorrow_vis_class,
            "dayafter_vis_class": dayafter_vis_class,
            "calendar_summary": calendar_summary,
            "next_event_text": next_event_text,
        }

        # Add day 2 params
        if num_cal_days >= 2:
            params.update({
                "tomorrow": (current_date + timedelta(days=1)).strftime("%A"),
                "events_tomorrow": cal_events_list[1],
                "col_tomorrow_width": col_tomorrow_width
            })
        else:
            # Default values for tomorrow
            params.update({
                "tomorrow": "",
                "events_tomorrow": "",
                "col_tomorrow_width": col_tomorrow_width
            })

        # Add day 3 params
        if num_cal_days >= 3:
            params.update({
                "dayafter": (current_date + timedelta(days=2)).strftime("%A"),
                "events_dayafter": cal_events_list[2],
            })
        else:
            # Default values for day after tomorrow
            params.update({
                "dayafter": "",
                "events_dayafter": "",
            })

        # Write out the HTML file
        htmlFile = open(self.currPath + '/dashboard.html', "w")
        htmlFile.write(dashboard_template.format(**params))
        htmlFile.close()

        # Take the screenshot
        self.get_screenshot(path_to_server_image)
