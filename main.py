import network, urequests, time, ntptime
from machine import Pin, I2C
import pico_i2c_lcd

ssid = "YourSSID"
password = "YourPassword"

# I2C LCDs
i2c0 = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
lcd1 = pico_i2c_lcd.I2cLcd(i2c0, 0x27, 2, 16)

i2c1 = I2C(1, scl=Pin(19), sda=Pin(18), freq=400000)
lcd2 = pico_i2c_lcd.I2cLcd(i2c1, 0x27, 2, 16)

URL = "http://wttr.in/Ulceby?format=j1"
TZ_OFFSET = 0   # adjust for timezone

def localtime():
    return time.localtime(time.time() + TZ_OFFSET*3600)

def lcd_print(lcd, row, text):
    lcd.move_to(0, row)
    lcd.putstr("{:<16}".format(text))

def show_today(d):
    temp = d["current_condition"][0]["temp_C"]
    hum = d["current_condition"][0]["humidity"]
    desc = d["current_condition"][0]["weatherDesc"][0]["value"]
    lcd1.clear()
    lcd_print(lcd1, 0, f"Now:{temp}C {hum}%")
    lcd_print(lcd1, 1, desc[:16])

def show_forecast(d, day_index, label):
    day = d["weather"][day_index]
    maxtemp = day["maxtempC"]
    mintemp = day["mintempC"]
    desc = day["hourly"][4]["weatherDesc"][0]["value"]
    lcd1.clear()
    lcd_print(lcd1, 0, f"{label}:{mintemp}-{maxtemp}C")
    lcd_print(lcd1, 1, desc[:16])

def show_average(d):
    conditions = []
    for i in range(3):
        for h in d["weather"][i]["hourly"]:
            conditions.append(h["weatherDesc"][0]["value"].lower())
    keywords = ["rain", "sun", "wind", "thunder", "breeze", "cloud"]
    counts = {k:0 for k in keywords}
    for c in conditions:
        for k in keywords:
            if k in c:
                counts[k] += 1
    avg = max(counts, key=counts.get) if any(counts.values()) else "mixed"
    avg_str = str(avg)
    avg_str = avg_str[0].upper() + avg_str[1:] if len(avg_str) > 1 else avg_str.upper()
    lcd1.clear()
    lcd_print(lcd1, 0, "Average Weather")
    lcd_print(lcd1, 1, avg_str)

def fetch_with_timeout(url, timeout=10):
    start = time.time()
    while True:
        try:
            return urequests.get(url)
        except Exception:
            if time.time() - start > timeout:
                raise OSError("Request timed out")
            time.sleep(1)

# --- Wi-Fi connect ---
lcd1.clear(); lcd_print(lcd1, 0, "Connecting to"); lcd_print(lcd1, 1, "server...")
lcd2.clear(); lcd_print(lcd2, 0, "Connecting to"); lcd_print(lcd2, 1, "server...")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

timeout = 20
start = time.time()
while not wlan.isconnected() and time.time() - start < timeout:
    time.sleep(0.5)

if not wlan.isconnected():
    lcd1.clear(); lcd_print(lcd1, 0, "Wi-Fi Error"); lcd_print(lcd1, 1, "Check SSID/PW")
    lcd2.clear(); lcd_print(lcd2, 0, "Wi-Fi Error"); lcd_print(lcd2, 1, "Check Router")
    raise SystemExit

ip = wlan.ifconfig()[0]
lcd1.clear(); lcd_print(lcd1, 0, "Connected IP:"); lcd_print(lcd1, 1, ip)
lcd2.clear(); lcd_print(lcd2, 0, "Connected IP:"); lcd_print(lcd2, 1, ip)
time.sleep(3)

ntptime.settime()

# --- Timers ---
last_clock_update = 0
last_weather_update = 0
last_page_update = 0
weather_interval = 60   # refresh data every 60s
page_interval = 10      # change page every 10s
page = 0
data = None

while True:
    now = time.time()

    # Update clock every second
    if now - last_clock_update >= 1:
        t = localtime()
        date_str = "{:02d}/{:02d}/{:04d}".format(t[2], t[1], t[0])
        time_str = "{:02d}:{:02d}".format(t[3], t[4])
        lcd2.clear()
        lcd_print(lcd2, 0, date_str)
        lcd_print(lcd2, 1, time_str)
        last_clock_update = now

    # Fetch weather every 60s
    if now - last_weather_update >= weather_interval or data is None:
        try:
            response = fetch_with_timeout(URL, timeout=10)
            data = response.json()
            response.close()
            last_weather_update = now
        except Exception:
            lcd1.clear()
            lcd_print(lcd1, 0, "Error")

    # Change weather page every 10s
    if data and now - last_page_update >= page_interval:
        if page == 0:
            show_today(data)
        elif page == 1:
            show_forecast(data, 1, "Tomorrow")
        elif page == 2:
            show_forecast(data, 2, "DayAfter")
        elif page == 3:
            show_average(data)
        page = (page + 1) % 4
        last_page_update = now

    time.sleep_ms(200)  # small pause to avoid busy loop
