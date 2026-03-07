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
import os
from selenium.webdriver.common.by import By


class RenderHelper:

    def __init__(self, width, height, timeFormat=12):
        self.logger = logging.getLogger('maginkdash')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.htmlFile = 'file://' + self.currPath + '/dashboard.html'
        self.imageWidth = width
        self.imageHeight = height
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
        all_event_list,
        path_to_server_image,
        ignore_patterns=None,
    ):
        # Always prepare three days (today + next two days)
        max_display_days = min(3, len(all_event_list)) if all_event_list else 1
        event_list = all_event_list[:max_display_days]

        # Filter out events matching any ignore pattern
        if ignore_patterns:
            import re
            compiled = [re.compile(p, re.IGNORECASE) for p in ignore_patterns]
            event_list = [
                [e for e in day if not any(p.search(e['summary']) for p in compiled)]
                for day in event_list
            ]

        # Pad with empty lists if fewer than three days are available
        while len(event_list) < 3:
            event_list.append([])

        # Load and shuffle SVGs for empty state display
        import random
        empty_state_dir = os.path.join(self.currPath, 'empty_states')
        svg_files = sorted([f for f in os.listdir(empty_state_dir) if f.endswith('.svg')])
        random.shuffle(svg_files)
        svg_index = 0
        with open(self.currPath + '/dashboard_template.html', 'r') as file:
            dashboard_template = file.read()

        # Populate the date and events
        cal_events_list = []
        for i in range(3):
            day_events = event_list[i] if i < len(event_list) else []
            cal_events_text = ""

            if len(day_events) == 0:
                svg_content = ""
                if svg_files:
                    import re as _re
                    svg_path = os.path.join(empty_state_dir, svg_files[svg_index % len(svg_files)])
                    svg_index += 1
                    with open(svg_path, 'r') as f:
                        svg_content = f.read()
                    # Remove hardcoded width/height from <svg> tag so CSS can control size
                    svg_content = _re.sub(r'(<svg[^>]*)\s+width="[^"]*"', r'\1', svg_content)
                    svg_content = _re.sub(r'(<svg[^>]*)\s+height="[^"]*"', r'\1', svg_content)
                cal_events_text = (
                    '<li class="nothing-today"><div class="event-title">Nothing to do!</div></li>'
                    '<li class="empty-state-svg">' + svg_content + '</li>'
                )
            else:
                # Group all-day and timed events
                allday_events = [e for e in day_events if e["isMultiday"] or e["allday"]]
                timed_events  = [e for e in day_events if not e["isMultiday"] and not e["allday"]]

                if allday_events:
                    cal_events_text += '<li class="event allday"><div class="event-time">All day</div>'
                    for e in allday_events:
                        cal_events_text += '<div class="event-title">• ' + e['summary'] + '</div>'
                    cal_events_text += '</li>\n'

                for event in timed_events:
                    cal_events_text += (
                        '<li class="event">'
                        '<div class="event-time">' + self.get_short_time(event['startDatetime']) + '</div>'
                        '<div class="event-title">' + event['summary'] + '</div>'
                        '</li>\n'
                    )

            cal_events_list.append(cal_events_text)

        # Build the params dictionary for template formatting
        params = {
            "day": current_date.strftime("%-d"),
            "month": current_date.strftime("%B"),
            "weekday": current_date.strftime("%A"),
            "today_empty": 'empty' if len(event_list[0]) == 0 else '',
            "events_today": cal_events_list[0],
            "tomorrow": (current_date + timedelta(days=1)).strftime("%A"),
            "tomorrow_day": (current_date + timedelta(days=1)).strftime("%-d"),
            "tomorrow_month": (current_date + timedelta(days=1)).strftime("%B"),
            "tomorrow_empty": 'empty' if len(event_list[1]) == 0 else '',
            "events_tomorrow": cal_events_list[1],
            "dayafter": (current_date + timedelta(days=2)).strftime("%A"),
            "dayafter_day": (current_date + timedelta(days=2)).strftime("%-d"),
            "dayafter_month": (current_date + timedelta(days=2)).strftime("%B"),
            "dayafter_empty": 'empty' if len(event_list[2]) == 0 else '',
            "events_dayafter": cal_events_list[2],
        }

        # Write out the HTML file
        with open(self.currPath + '/dashboard.html', "w") as htmlFile:
            htmlFile.write(dashboard_template.format(**params))

        # Take the screenshot
        self.get_screenshot(path_to_server_image)