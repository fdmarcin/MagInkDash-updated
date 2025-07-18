# MagInkDash - updated

This repo contains the code needed to drive an e-ink magic dashboard that uses a Raspberry Pi to:

- Automatically retrieve updated content from Google Calendar and OpenWeatherMap.
- Format it into the desired layout.
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

1. A `cron` job on RPi triggers a Python script to run every hour to fetch calendar events from Google Calendar and weather forecast from OpenWeatherMap.
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

- **Telegram Bot**:

  Although the battery life is crazy long on the Inkplate 10, I still wish to be notified when the battery runs low.
  To do so, I set up a Telegram Bot and the Inkplate triggers the bot to send me a message if the measured battery voltage falls below a specified threshold.
  That said, with the bot set up, there's actually much more you could do, for example, send yourself a message when it's to expected to rain in the next hour.

![MagInkDash Features](https://user-images.githubusercontent.com/5581989/231484018-6ff6a883-3226-42c7-a387-fcef7ee9d49c.png)

## Setting up

### Prepare the RaspberryPi

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
   sudo apt install -y python3-pip chromium-chromedriver libopenjp2-7-dev
   sudo apt install apache2 -y
   pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
   pip3 install pytz selenium Pillow
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

   If you can't authorize the app in the browser:

   - Clear your browser cache and cookies or paste the authorization URL in an incognito window.
   - If you run the script while connected to the RPi through SSH and open the URL on your local machine, the final redirect likely fails.
     You should do it on the same machine.

1. Fill out the config file [`config.json`](./config.json):

   - `displayTZ`: Set to your timezone. Use the [TZ identifier format](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List).
   - `calendars`: `primary` is your main calendar.
     To add more, get their IDs from Google Calendar settings.
     For example: `["primary", "example@import.calendar.google.com"]`
   - `max_events_per_day` and `max_total_events` to limit the maximum of events shown.
   - `timeFormat`: To format calendar times using the 24-hour clock, change the value to `24`.
   - `owm_api_key`: Enter your OpenWeatherMap API key.
     I used the "Pay as you call" [One Call API 3.0](https://openweathermap.org/api).
   - `lat` and `lon`: Set to your location's latitude and longitude for weather.
   - `imageWidth` and `imageHeight` should match the resolution of your display.
     `1200` and `825` match Inkplate 10.

1. The script to generate the dashboard should work now!
   To test it manually, run the following in the `MagInkDash-updated` folder:

   ```bash
   python3 main.py
   ```

1. Write down the URL of the generated image.

   When you installed the Apache 2 package earlier, an Apache server started automatically.
   To confirm whether this web server is running or not, run the following command:

   ```bash
   sudo service apache2 status
   ```

   From now on, Apache will automatically serve anything that's in the `/var/www/html` folder. That's where our script puts the generated image.
   To get the URL for it, substitute `/var/www/html` with your Pi's IP address or URL (in the format of `<hostname>.local`, for example, `raspberrypi.local`). Then, the generated image should be visible at http://raspberrypi.local/maginkdash.png.

   However, if you don’t know the IP address of your Raspberry Pi, run the command below in the terminal of your Raspberry Pi:

   ```bash
   hostname -I
   ```

   The server you just set up is only accessible for people connected to your home network and it's
   not accessible through the internet.
   To make this server accessible from anywhere, you'd need to set up port forwarding on your router.

1. Copy all the files (other than the `inkplate` folder) over to your RPi using your preferred means.

1. In the RPi Terminal, run the following command. This is where you'll define scheduled execution
   of the code to regenerate your dashboard.

   ```bash
   crontab -e
   ```

1. Add a command to crontab so your RPi knows when to run the MagInkDash Python script.

   For example, every day, on the hour, every hour:

   ```bash
   0 * * * * cd /location/to/your/MagInkDash-updated && python3 main.py
   ```

   Monday to Friday, on the hour, every hour, from 9 am to 9 pm:

   ```bash
   0 9-21 * * 1-5 cd /location/to/your/MagInkDash-updated && python3 main.py
   ```

### Configure the Inkplate

1. Optional. Create a Telegram bot:
   1. Sign in to Telegram and find [@BotFather](https://telegram.me/BotFather).
   1. Select **Start** or **Start bot**.
   1. In the chat, send `/newbot`.
   1. Choose a name for your bot, for example, `MagInkDash battery level`.
   1. Choose a username for your bot.
   1. When you see a success message, write down the token you get for later.
      Don't share it with anyone.
   1. Click the `t.me` link to your bot and select **Start**.
      This is the bot that will message you on Telegram when your Inkplate battery is low.
      You can customize its profile picture and description in the chat **Manage Bot** option.
   1. Find [`@myidbot`](https://t.me/myidbot), select **Start** and send `/getid`.
      Write down your Telegram ID for later.
1. Follow the [official resources](https://inkplate.readthedocs.io/en/latest/get-started.html)
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

1. In the Arduino IDE, select **Tools > Manage Libraries**, search for `UniversalTelegramBot` and select **Install** next to it.
   If you're prompted to also install its dependency, agree to it.

1. In the Arduino IDE, open the `inkplate/inkplate.ino` file and upload it when connected to the Inkplate.

   When prompted to select the serial port, on Linux you should probably select `/dev/ttyUSB0`.
   If you get an error, follow [the official steps](https://docs.arduino.cc/software/ide-v1/tutorials/Linux/#please-read), then log out and back in.
   Also, change upload speed to `115200` in Arduino IDE **Tools > Upload speed**.

1. That's all! Your Magic Dashboard should now be refreshed every hour!

![20230412_214652](https://user-images.githubusercontent.com/5581989/231485348-35d7e0df-034e-49aa-8500-223b2b3bdcc0.JPG)

![20230412_215020](https://user-images.githubusercontent.com/5581989/231484068-aa6ce877-1e0a-49fe-b47e-7c024752f42c.JPG)

Selfie and family portrait together with the MagInkCal

## Troubleshooting

### Google Calendar token expired or was revoked

One disdvantage of creating a Google Cloud app whose publishing status is **Testing**, is that
[your token expires after 7 days](https://support.google.com/cloud/answer/15549945?sjid=5497909174448144541-EU#publishing-status&zippy=%2Ctesting).
You will get this error when running the script.

You could consider [publishing your app](https://daniel.es/blog/publishing-your-google-cloud-project-app-ask-for-your-google-app-to-be-published/).

Prerequisites:

- Either boot RaspberryPi in graphical mode or do it in the copy of the repository on your PC.
  - If doing this on your PC, make sure to install the `pip3` dependencies and move `credentials.json` to the `gcal` folder.

To fix this:

1. Go to the `gcal` folder.
1. Delete `token.pickle`: `rm token.pickle`.
1. Run the following command:

   ```bash
   python3 quickstart.py
   ```

   A web browser should appear, asking you to sign into Google and grant access to your calendar.
   Once done, you should see a `token.pickle` file in your `gcal` folder.

If you can't authorize the app in the browser:

- Clear your browser cache and cookies or paste the authorization URL in an incognito window.
- If you run the script while connected to the RPi through SSH and open the URL on your local machine, the final redirect likely fails.
  You should do it on the same machine.
- Create a new [Calendar API client](https://console.cloud.google.com/auth/clients) and configure it as "Desktop app".
  Save the generated JSON file as `credentials.json` like before and follow the troubleshooting steps again.
- Add your email address under [Test users](https://console.cloud.google.com/auth/audience).

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

- Deleted OpenAI API integration (if you want to use it, see branch [`openAI-trivia`](https://github.com/fdmarcin/MagInkDash-updated/tree/openAI-trivia))
- OpenWeatherMap API
  - Improved error handling and logging for weather data retrieval.
  - Added robust defaults for missing or incomplete weather data.
  - Ensured compatibility with the current One Call API (v3.0).
- Google Calendar API
  - Fix for displaying 2 or 1 calendar days.
  - Added a configurable 12/24-hour time format option in `config.json`.
- Improved Chromedriver detection
  - Added smart auto-detection of chromedriver location using `which chromedriver`.
  - Implemented fallback to common installation locations if auto-detection fails.
  - Added helpful error messages and logging for troubleshooting.
  - Enhanced error handling during the screenshot process.
- Added time format configuration
  - Implemented time formatting throughout the application that respects the user's preference.
  - Added graceful handling of missing configuration with sensible defaults.
- Better output and logging
  - Added display of the absolute path to the generated image for easier verification.
  - Improved logging throughout the application.
  - Added informative messages about time format and other configuration options.
- General code improvements
  - Enhanced error handling throughout the codebase.
  - Added more detailed logging.
  - Improved resource management (properly closing webdriver with `driver.quit()`).
  - Added configuration parameters with sensible defaults for better backward compatibility.

These updates make MagInkDash compatible with current APIs, more user-friendly, and more robust in various environments, particularly on headless Raspberry Pi systems.

See original README at <https://github.com/speedyg0nz/MagInkDash/blob/main/README.md>.