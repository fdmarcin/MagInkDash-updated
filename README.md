# MagInkDash - updated

This repo contains the code needed to drive an e-ink magic dashboard that uses a Raspberry Pi to:

- Automatically retrieve updated content from Google Calendar, OpenWeatherMap and OpenAI ChatGPT
- Format it into the desired layout
- Serve it to a battery-powered e-ink display (Inkplate 10).

> [!NOTE]
> The code has only been tested on the specific hardware mentioned, but can be easily modified to work with other hardware (for both the server or display).

![20230412_214635](https://user-images.githubusercontent.com/5581989/231482915-154db674-9301-465d-8352-d2c4400093eb.JPG)

## Hardware required

- [Raspberry Pi](https://www.raspberrypi.org/):

  Used as a server to retrieve content and generate a dashboard for the E-Ink display so any model would do.
  Personally, I used a Raspberry Pi 3 B+ from 2016 and it works fine for this purpose.
  In fact, it doesn't even need to be a RPi.
  Any other Single Board Computer, or old computer, or even a cloud service that runs the code would suffice.
- [Inkplate 10 Battery Powered E-Ink Display](https://soldered.com/product/soldered-inkplate-10-9-7-e-paper-board-with-enclosure-copy/):

   Used as a client to display the generated dashboard.
   I went with this because it was an all-in-one with the enclosure and battery included so there's less hardware tinkering.
   But you could certainly go barebones and assemble the different parts yourself from scratch, that is, display, microcontroller, case, and battery.

## How it works

1. A `cron` job on RPi triggers a Python script to run every hour to fetch calendar events from Google Calendar, weather forecast from OpenWeatherMap and random factoids from OpenAI's ChatGPT.
1. The retrieved content is then formatted into the desired layout and saved as an image.
1. An Apache server on the RPi hosts this image such that it can be accessed by the Inkplate 10.
1. On the Inkplate 10, the corresponding script then connects to the RPi server on the local network
   via a WiFi connection, retrieves the image and displays it on the E-Ink screen.
1. The Inkplate 10 then goes to sleep to conserve battery. The dashboard remains displayed on the E-Ink screen, because well, E-Ink...

Some features of the dashboard:

- **Battery Life**:

  As with similar battery powered devices, the biggest question is the battery life. I'm currently using a 1500mAh battery on the Inkplate 10 and based on current usage, it should last me around 3-4 months. With the 3000mAh that comes with the manufacturer assembled Inkplate 10, we could potentially be looking at 6-8 month battery life. With this crazy battery life, there are much more options available. Perhaps solar power for unlimited battery life? Or reducing the refresh interval to 15 or 30min to increase the information timeliness?
- **Calendar and Weather**:

  I'm currently displaying calendar events and weather forecast for current day and the upcoming two days.
  No real reason other than the desire to know what my weekend looks like on a Friday, and therefore helping me to better plan my weekend.
  Unfortunately, if you have a busy calendar with numerous events on a single day, the space on the dashboard is consumed very quickly.
  If so, you might wish to modify the code to reduce/limit the number of days/events to be displayed by setting `"numCalDaysToShow"` in `config.json` to a different value.
- **OpenAI ChatGPT**:

  AI is everywhere now.
  There's a section in the dashboard to retrieve ChatGPT responses via OpenAI's API (free but you have to spend minimum 5 USD on credit).
  So far I'm using it to retrieve factoids on animals, historical figures, notable events, countries, world records, etc.
  The prompts fed to ChatGPT can certainly be customised, so please knock yourself out and think of the most outrageous things you can put on your dashboard.
  Note that you might have to test and adjust the prompts/parameters, else ChatGPT might return fairly repetitive responses, for example, on Abraham Lincoln, Rosa Parks, Martin Luther King.
- **Telegram Bot**:

  Although the battery life is crazy long on the Inkplate 10, I still wish to be notified when the battery runs low.
  To do so, I set up a Telegram Bot and the Inkplate triggers the bot to send me a message if the measured battery voltage falls below a specified threshold.
  That said, with the bot set up, there's actually much more you could do, for example, send yourself a message when it's to expected to rain in the next hour.

![MagInkDash Features](https://user-images.githubusercontent.com/5581989/231484018-6ff6a883-3226-42c7-a387-fcef7ee9d49c.png)

## Setting up

1. Flash [Raspberrypi OS](https://www.raspberrypi.org/software/operating-systems/) to a SD/MicroSD Card.

   If you're using a Raspberry Pi with 32-bit CPU, there are [known issues](https://forums.raspberrypi.com/viewtopic.php?t=323478) between the latest RPiOS "bullseye" release and `chromium-browser`, which is required to run this code. As such, I would recommend that you keep to the legacy `buster` OS if you're still running this on older RPi hardware.

1. After setting up the OS, run the following commmand in the RPi Terminal, and use the [`raspi-config`](https://www.raspberrypi.org/documentation/computers/configuration.html) interface to setup Wifi connection, and set the timezone to your location.
   You can skip this if the image is already preconfigured using the Raspberry Pi Imager.

   ```bash
   sudo raspi-config
   ```

1. Run the following commands in the RPi Terminal to setup the environment to run the Python scripts and function as a web server.
   It'll take some time so be patient here.

   If you changed your username during `raspi-config`, change the `chown` command to use it instead of `pi`.

   ```bash
   sudo apt update
   sudo apt install -y python3-pip chromium-chromedriver libopenjp2-7-dev apache2
   pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
   pip3 install pytz selenium Pillow openai
   sudo chown pi:www-data /var/www/html
   sudo chmod 755 /var/www/html
   ```

1. Download the files in this repo to a folder in your PC.
1. To access your Google Calendar events, it's necessary to first grant the access.
   Follow [Google's Python quick start](https://developers.google.com/calendar/api/quickstart/python)
   on your PC to get the `credentials.json` file from your Google API.
   Don't worry, take your time.
   I'll be waiting here.

1. When done, copy the `credentials.json` file to the `gcal` folder in this project.
   Go to the `gcal` folder and run the following command on your PC.
   A web browser should appear, asking you to sign into Google and grant access to your calendar.
   Once done, you should see a `token.pickle` file in your `gcal` folder.

   ```bash
   python3 quickstart.py
   ```

1. Fill out the config file [`config.json`](./config.json):

   - `displayTZ`: Set to your timezone. Use the [TZ identifier format](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List).
   - `timeFormat`: To format calendar times using the 24-hour clock, change the value to `24`.
   - `owm_api_key`: Enter your OpenWeatherMap API key.
     I used the "Pay as you call" [One Call API 3.0](https://openweathermap.org/api).
   - `lat` and `lon`: Set to your location's latitude and longitude for weather.
   - `imageWidth` and `imageHeight` should match the resolution of your display.
     `1200` and `825` match Inkplate 10.
   - `openai_api_key`: Enter your [OpenAI API key](https://platform.openai.com/settings/organization/api-keys).
     I paid 5 USD to get into the [Usage tier 1](https://platform.openai.com/settings/organization/limits) and get free requests.

1. Copy all the files (other than the `inkplate` folder) over to your RPi using your preferred means.

1. Run the following command in the RPi Terminal to open crontab.

   ```bash
   crontab -e
   ```

1. Add a command to crontab so your RPi knows when to run the MagInkDash Python script.

   For example:

   ```bash
   # Every day, on the hour, every hour:
   0 * * * * cd /location/to/your/MagInkDash && python3 main.py
   ```

   ```bash
   # Monday to Friday, on the hour, every hour:
   0 * * * 1-5 cd /location/to/your/MagInkDash && python3 main.py
   ```

1. Configure the Inkplate.
   Follow the [official resources](https://inkplate.readthedocs.io/en/latest/get-started.html)
   (only the Arduino portion of the guide is relevant).
   It can take some trial and error for those new to microcontroller programming but it's all worth it!
   You'll need to be able to run `*.ino` scripts via Arduino IDE before proceeding.

1. Edit the following lines in `inkplate/inkplate.ino` to add your wi-fi details and optionally configure
   your Telegram bot to message you when the battery is low:

   ```cpp
   const char ssid[] = "YOUR WIFI SSID";    // Your WiFi SSID
   const char *password = "YOUR WIFI PASSWORD"; // Your WiFi password
   const char *imgurl = "http://url.to.your.server/maginkdash.png"; // Your dashboard image web address

   // Initialize Telegram BOT
   #define BOTtoken "YOUR TELEGRAM BOT TOKEN"  // your Bot Token (Get from Botfather)

   // Use @myidbot to find out the chat ID of an individual or a group
   // Also note that you need to click "start" on a bot before it can
   // message you
   #define CHAT_ID "YOUR TELEGRAM CHAT ID TO SEND MESSAGES TO"

   // Battery values
   #define BATTV_MAX    4.1     // maximum voltage of battery
   #define BATTV_MIN    3.2     // what we regard as an empty battery
   #define BATTV_LOW    3.4     // voltage considered to be low battery
   ```

1. From the Arduino IDE, run the `inkplate/inkplate.ino` file when connected to the Inkplate.

1. That's all! Your Magic Dashboard should now be refreshed every hour!

![20230412_214652](https://user-images.githubusercontent.com/5581989/231485348-35d7e0df-034e-49aa-8500-223b2b3bdcc0.JPG)

![20230412_215020](https://user-images.githubusercontent.com/5581989/231484068-aa6ce877-1e0a-49fe-b47e-7c024752f42c.JPG)

Selfie and family portrait together with the MagInkCal

## Acknowledgements

- [Lexend Font](https://fonts.google.com/specimen/Lexend) and [Tilt Warp Font](https://fonts.google.com/specimen/Tilt+Warp): Fonts used for the dashboard display.
- [Bootstrap](https://getbootstrap.com/): Styling toolkit to customise the look of the dashboard.
- [Weather Icons](https://erikflowers.github.io/weather-icons/): Icons used for displaying of weather forecast information.
- [Freepik](https://www.freepik.com/): For the background image used in this dashboard.
- [speedyg0nz](https://github.com/speedyg0nz): For [the original project](https://github.com/speedyg0nz/MagInkDash).

## Contributing

I won't be updating this code much, since it serves my needs well.
Nevertheless, feel free to fork the repo and modify it for your own purpose.
At the same time, check out other similar projects, such as [InkyCal](https://github.com/aceisace/Inkycal) by [/u/aceisace](https://www.reddit.com/user/aceisace/).
It's much more polished and also actively developed.

## Differences from upstream project

What I've changed compared to https://github.com/speedyg0nz/MagInkDash:

<details>
<summary>Click to expand</summary>

1. Updated OpenAI API integration

   - Migrated from the deprecated `openai.Completion.create()` method to the modern client-based approach using `from openai import OpenAI`.
   - Updated from the deprecated `text-davinci-003` model to `gpt-3.5-turbo`.
   - Modified the prompt format to use the required chat completion format with messages array.
   - Updated response parsing to match the new API structure.

1. Enhanced OpenWeatherMap API usage

   - Improved error handling and logging for weather data retrieval.
   - Added robust defaults for missing or incomplete weather data.
   - Ensured compatibility with the current One Call API (v3.0).

1. Improved Chromedriver detection

   - Added smart auto-detection of chromedriver location using `which chromedriver`.
   - Implemented fallback to common installation locations if auto-detection fails.
   - Added helpful error messages and logging for troubleshooting.
   - Enhanced error handling during the screenshot process.

1. Added time format configuration

   - Added a configurable 12/24-hour time format option in `config.json`.
   - Implemented time formatting throughout the application that respects the user's preference.
   - Added graceful handling of missing configuration with sensible defaults.

1. Better output and logging

   - Added display of the absolute path to the generated image for easier verification.
   - Improved logging throughout the application.
   - Added informative messages about time format and other configuration options.

1. General code improvements

   - Enhanced error handling throughout the codebase.
   - Added more detailed logging.
   - Improved resource management (properly closing webdriver with `driver.quit()`).
   - Added configuration parameters with sensible defaults for better backward compatibility.

These updates make MagInkDash compatible with current APIs, more user-friendly, and more robust in various environments, particularly on headless Raspberry Pi systems.

</details>

See original README at <https://github.com/speedyg0nz/MagInkDash/blob/main/README.md>.