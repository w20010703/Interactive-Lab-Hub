#!/usr/bin/env python3
# Raspberry Pi 5 + Adafruit Mini PiTFT 1.14" (ST7789)
# + STEMMA QT Rotary Encoder (I2C @ 0x36)
# Press encoder to start/stop recording; recognized speech appears on the display.

import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from PIL import Image, ImageDraw, ImageFont
import digitalio, board, busio
import adafruit_rgb_display.st7789 as st7789
from adafruit_seesaw import seesaw, rotaryio, digitalio as seesaw_dio

# ------------------------------------------------------------
# DISPLAY SETUP
# ------------------------------------------------------------
cs_pin = digitalio.DigitalInOut(board.D5)       # GPIO5 (pin 29)
dc_pin = digitalio.DigitalInOut(board.D25)      # GPIO25 (pin 22)
reset_pin = None
BAUDRATE = 64_000_000
spi = board.SPI()                               # /dev/spidev0.0

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

font = ImageFont.load_default()
DRAW_W, DRAW_H = 240, 135

# ------------------------------------------------------------
# ROTARY ENCODER (STEMMA QT)
# ------------------------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
ss = seesaw.Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(ss)
button = seesaw_dio.DigitalIO(ss, 24)
button.switch_to_input()  # Seesaw has built-in pull-up
last_button_state = button.value

# ------------------------------------------------------------
# SPEECH RECOGNITION
# ------------------------------------------------------------
recognizer = sr.Recognizer()
recording = False
audio_buffer = []

# ------------------------------------------------------------
# DISPLAY HELPER (word wrap + clipping)
# ------------------------------------------------------------
def show_text(text, color=(255,255,255), bg=(0,0,0)):
    """Render wrapped text on TFT in landscape orientation."""
    img = Image.new("RGB", (DRAW_W, DRAW_H), bg)
    draw = ImageDraw.Draw(img)
    margin, offset = 5, 5
    max_width = DRAW_W - 2*margin
    line_height = font.getbbox("A")[3] + 2

    words = text.split()
    line = ""
    lines = []

    # Wrap text manually
    for word in words:
        test_line = line + (" " if line else "") + word
        w = draw.textlength(test_line, font=font)
        if w <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
        if (offset + len(lines)*line_height) >= (DRAW_H - line_height):
            break
    if line:
        lines.append(line)

    # Draw visible lines only
    for i, l in enumerate(lines[:DRAW_H // line_height]):
        draw.text((margin, offset + i*line_height), l, fill=color, font=font)
    if len(lines) * line_height > DRAW_H - 2*line_height:
        draw.text((DRAW_W - 20, DRAW_H - line_height), "...", fill=color, font=font)

    rotated = img.rotate(90, expand=True)
    display.image(rotated)

# ------------------------------------------------------------
# AUDIO + RECOGNITION
# ------------------------------------------------------------
def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audio stream:", status)
    audio_buffer.append(indata.copy())

def start_recording():
    global audio_buffer
    audio_buffer = []
    show_text("Recording...", color=(0,255,0))
    print("Recording started")
    return sd.InputStream(samplerate=16000, channels=1, dtype="int16", callback=audio_callback)

def stop_and_transcribe():
    global audio_buffer
    if not audio_buffer:
        show_text("(no audio)", color=(255,255,0))
        return
    show_text("Processing...", color=(255,255,0))
    print("Processing...")
    audio_data = np.concatenate(audio_buffer)
    audio_obj = sr.AudioData(audio_data.tobytes(), 16000, 2)
    try:
        text = recognizer.recognize_google(audio_obj)
        print("Heard:", text)
        show_text(text, color=(255,255,255))
    except sr.UnknownValueError:
        show_text("(unrecognized)", color=(255,0,0))
    except sr.RequestError:
        show_text("(network error)", color=(255,0,0))

# ------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------
print("Press encoder to start/stop recording. Ctrl+C to exit.")
stream = None

while True:
    if button.value == False and last_button_state == True:
        time.sleep(0.1)
        if not recording:
            recording = True
            stream = start_recording()
            stream.start()
        else:
            recording = False
            if stream:
                stream.stop()
                stream.close()
            stop_and_transcribe()
    last_button_state = button.value
    time.sleep(0.05)
