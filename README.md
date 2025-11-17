# Dual-LCD Weather Station (Raspberry Pi Pico W)

This project displays weather forecasts and a clock on two I²C LCDs.

## Features
- Wi-Fi connect animation with timeout
- NTP time sync with timezone offset
- LCD1 cycles through:
  - Current conditions
  - Tomorrow forecast
  - Day After forecast
  - Average weather summary
- LCD2 shows date + time (hours:minutes only)
- Smooth loading animation
- Error handling for Wi-Fi and weather fetch

## Hardware
- Raspberry Pi Pico W
- 2x I²C 16x2 LCDs (address 0x27)
- Wi-Fi network (2.4GHz)

## Setup
1. Flash MicroPython firmware on Pico W.
2. Install `pico_i2c_lcd` library.
3. Update `ssid` and `password` in `main.py`.
4. Upload files to Pico W.
5. Run `main.py`.

## License
MIT
