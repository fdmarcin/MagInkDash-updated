#if !defined(ARDUINO_INKPLATE10) && !defined(ARDUINO_INKPLATE10V2)
#error "Wrong board selection for this example, please select e-radionica Inkplate10 or Soldered Inkplate10 in the boards menu."
#endif

#include "Inkplate.h"
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>
#include <ArduinoJson.h>

Inkplate display(INKPLATE_3BIT);

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

WiFiClientSecure client;
UniversalTelegramBot bot(BOTtoken, client);

void setup()
{
    Serial.begin(115200);
    display.begin();

    // Connect to WiFi
    Serial.print("Connecting to WiFi...");
    WiFi.begin(ssid, password);

    // Wait for connection
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("Connected!");

    // Retrieve and display image
    Serial.print("Downloading image...");
    char url[256];
    strcpy(url, imgurl);
    Serial.println(display.drawImage(url, display.PNG, 0, 0));
    display.display();

    //uncomment or delete the following section if not using Telegram to send message when battery is low
    double battvoltage = display.readBattery();
    int battpc = calc_battery_percentage(battvoltage);
    if (battvoltage < BATTV_LOW) {
        char msg [100];
        sprintf (msg, "Inkplate battery at %d%%, voltage at %.2fV", battpc, battvoltage);
        client.setCACert(TELEGRAM_CERTIFICATE_ROOT);
        bot.sendMessage(CHAT_ID, msg, "");
    }

    // Let display go to sleep to conserve battery, and wake up an hour later
    Serial.println("Going to sleep");
    delay(100);
    esp_sleep_enable_timer_wakeup(60ll * 60 * 1000 * 1000); //wakeup in 60min time - 60min * 60s * 1000ms * 1000us
    esp_deep_sleep_start();
}

void loop()
{
    // Never here, as deepsleep restarts esp32
}


int calc_battery_percentage(double battv)
{
    int battery_percentage = (uint8_t)(((battv - BATTV_MIN) / (BATTV_MAX - BATTV_MIN)) * 100);

    if (battery_percentage < 0)
        battery_percentage = 0;
    if (battery_percentage > 100)
        battery_percentage = 100;

    return battery_percentage;
}
