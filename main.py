"""
This project is designed for the Inkplate 10 display. However, since the server code is only generating an image, it can
be easily adapted to other display sizes and resolution by adjusting the config settings, HTML template and
CSS stylesheet.
As a dashboard, there are many other things that could be displayed, and it can be done as long as you are able to
retrieve the information. So feel free to change up the code and amend it to your needs.
"""

import datetime
import logging
import sys
import json
import os
from datetime import datetime as dt
from pytz import timezone
from gcal.gcal import GcalModule
from render.render import RenderHelper


if __name__ == '__main__':
    logger = logging.getLogger('maginkdash')

    # Basic configuration settings (user replaceable)
    configFile = open('config.json')
    config = json.load(configFile)

    calendars = config['calendars']  # Google Calendar IDs
    displayTZ = timezone(config['displayTZ'])  # list of timezones - print(pytz.all_timezones)
    imageWidth = config['imageWidth']  # Width of image to be generated for display.
    imageHeight = config['imageHeight']  # Height of image to be generated for display.
    rotateAngle = config['rotateAngle']  # If image is rendered in portrait orientation, angle to rotate to fit screen
    timeFormat = config.get('timeFormat', 12)  # 12 or 24-hour time format, default to 12 if not specified
    path_to_server_image = config["path_to_server_image"]  # Location to save the generated image

    # Create and configure logger
    logging.basicConfig(filename="logfile.log", format='%(asctime)s %(levelname)s - %(message)s', filemode='a')
    logger = logging.getLogger('maginkdash')
    logger.addHandler(logging.StreamHandler(sys.stdout))  # print logger to stdout
    logger.setLevel(logging.INFO)
    logger.info("Starting dashboard update")
    logger.info(f"Using {'24' if timeFormat == 24 else '12'}-hour time format")

    # Retrieve Calendar Data - get up to 3 days
    currDate = dt.now(displayTZ).date()
    calStartDatetime = displayTZ.localize(dt.combine(currDate, dt.min.time()))
    calEndDatetime = displayTZ.localize(dt.combine(currDate + datetime.timedelta(days=2), dt.max.time()))
    calModule = GcalModule()
    allEventList = calModule.get_events(
        currDate,
        calendars,
        calStartDatetime,
        calEndDatetime,
        displayTZ,
        3,
    )

    # Render Dashboard Image
    renderService = RenderHelper(imageWidth, imageHeight, rotateAngle, timeFormat)
    renderService.process_inputs(
        currDate,
        allEventList,
        path_to_server_image,
    )

    # Get absolute path to the generated image
    absolute_image_path = os.path.abspath(path_to_server_image)
    logger.info(f"Dashboard image saved to: {absolute_image_path}")

    logger.info("Completed dashboard update")