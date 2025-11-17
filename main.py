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

# Adjust for timezone (UK: 0 in winter, 1 in summer BST)
TZ_OFFSET = 0

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
    avg = str(max(counts, key=counts.get) if any(counts.values()) else "mixed")
    lcd1.clear()
    lcd_print(lcd1, 0, "Average Weather")
    lcd_print(lcd1, 1, avg.capitalize())

def animate_message(msg, lcdA, lcdB):
    dots = 0
    while True:
        text = msg + "." * (dots % 4)
        lcdA.clear()
        lcdB.clear()
        lcd_print(lcdA, 0, text)
        lcd_print(lcdB, 0, text)
        dots += 1
        yield
        time.sleep(0.2)

def fetch_with_timeout(url, timeout=10):
    start = time.time()
    while True:
        try:
            return urequests.get(url)
        except Exception:
            if time.time() - start > timeout:
                raise OSError("Request timed out")
            time.sleep(1)

# Connecting animation
lcd1.clear(); lcd_print(lcd1, 0, "Connecting to"); lcd_print(lcd1, 1, "server...")
lcd2.clear(); lcd_print(lcd2, 0, "Connecting to"); lcd_print(lcd2, 1, "server...")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

anim = animate_message("Connecting", lcd1, lcd2)
timeout = 20
start = time.time()
while not wlan.isconnected() and time.time() - start < timeout:
    next(anim)

if not wlan.isconnected():
    lcd1.clear(); lcd_print(lcd1, 0, "Wi-Fi Error"); lcd_print(lcd1, 1, "Check SSID/PW")
    lcd2.clear(); lcd_print(lcd2, 0, "Wi-Fi Error"); lcd_print(lcd2, 1, "Check Router")
    raise SystemExit

ip = wlan.ifconfig()[0]
lcd1.clear(); lcd_print(lcd1, 0, "Connected IP:"); lcd_print(lcd1, 1, ip)
lcd2.clear(); lcd_print(lcd2, 0, "Connected IP:"); lcd_print(lcd2, 1, ip)
time.sleep(3)

ntptime.settime()

last_weather_update = 0
weather_interval = 60
page = 0
data = None

while True:
    # Always update clock
    now = localtime()
    date_str = "{:02d}/{:02d}/{:04d}".format(now[2], now[1], now[0])
    time_str = "{:02d}:{:02d}".format(now[3], now[4])
    lcd2.clear()
    lcd_print(lcd2, 0, date_str)
    lcd_print(lcd2, 1, time_str)

    # Weather fetch only when interval passes
    if time.time() - last_weather_update > weather_interval or data is None:
        try:
            anim = animate_message("Loading", lcd1, lcd2)
            response = None
            while response is None:
                try:
                    next(anim)
                    response = fetch_with_timeout(URL, timeout=10)
                except Exception:
                    pass
            data = response.json()
            response.close()
            last_weather_update = time.time()
        except Exception:
            lcd1.clear()
            lcd_print(lcd1, 0, "Error")

    # Cycle weather pages if we have data
    if data:
        if page == 0:
            show_today(data)
        elif page == 1:
            show_forecast(data, 1, "Tomorrow")
        elif page == 2:
            show_forecast(data, 2, "DayAfter")
        elif page == 3:
            show_average(data)
        page = (page + 1) % 4
        time.sleep(10)

    ms = time.ticks_ms()
    time.sleep_ms(1000 - (ms % 1000))
