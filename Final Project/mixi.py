#!/usr/bin/env python3
"""
MIXI – SMART COCKTAIL MACHINE
Pi5 + MiniTFT + Rotary Encoder + Mic + AI Sentiment + Arduino Pump Control

Features:
- Record Mood (mic → speech → emotion classification)
- Mix Drink (uses emotion to pick recipe from YAML, with preview screen)
- Select Recipe (manual selection of the 6 emotion recipes)
- Pump Test (run individual pumps, scrollable, with Cancel)
- All recipes scaled to exactly 5 fl oz (148 mL) per drink
- Pump timing based on calibrated flow: 21.877 mL/s ≈ 45.7 ms per mL
- Optional background lounge music when Bluetooth is connected

Ingredient order (must match pump connections and YAML ml arrays):
Pump 0: black_tea
Pump 1: green_tea
Pump 2: rooibos_tea
Pump 3: chamomile_tea
Pump 4: lemon_tea
Pump 5: sparkling_water
"""

import os
import time
import serial
import yaml
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import subprocess  # for optional Bluetooth/music handling

# -------------------- OPENAI CLIENT ------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------- RPi HARDWARE IMPORTS ------------------
import board, busio, digitalio
import adafruit_rgb_display.st7789 as st7789
from adafruit_seesaw import seesaw, rotaryio, digitalio as seesaw_dio

# ------------------------------------------------------------
# CONSTANTS / CONFIG
# ------------------------------------------------------------
SERIAL_PORT = "/dev/ttyACM0"
BAUD = 9600

W, H = 240, 135  # buffer dimensions (portrait, will be rotated to landscape)

# Try a more elegant serif font; fall back to DejaVu Sans if missing
try:
    FONT = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 15
    )
except OSError:
    FONT = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15
    )

# Calibrated pump flow
FLOW_RATE_ML_PER_SEC = 21.877
MS_PER_ML = 45.7              # 1000 / FLOW_RATE_ML_PER_SEC ≈ 45.7 ms per mL
FIVE_OZ_ML = 148.0            # target total volume per drink

# Music / Bluetooth config
# Put your lounge music WAV file in the same folder and set this filename:
MUSIC_FILE = "lounge_loop.wav"   # you provide this file
# Optionally set your Bluetooth device MAC (e.g. "AA:BB:CC:DD:EE:FF") to only play when connected.
# If left as None, music will always play (route audio to Bluetooth via OS).
BT_DEVICE_MAC = None

music_proc = None  # subprocess handle for background music

# ------------------------------------------------------------
# LOAD YAML CONFIG (INGREDIENTS, EMOTIONS, RECIPES)
# ------------------------------------------------------------
with open("matrix.yaml", "r") as f:
    cfg = yaml.safe_load(f)

INGREDIENTS = cfg.get(
    "ingredients",
    [
        "black_tea",
        "green_tea",
        "rooibos_tea",
        "chamomile_tea",
        "lemon_tea",
        "sparkling_water",
    ],
)

EMOTIONS = cfg.get(
    "emotions",
    ["happiness", "sadness", "stress", "excitement", "calm", "surprise"],
)

RECIPES = cfg.get("recipes", {})

# Emotion → menu label mapping
RECIPE_MENU = [
    ("happiness", "Happiness — Golden Glow"),
    ("sadness", "Sadness — Warm Quiet Tea"),
    ("stress", "Stress — Stillness Cooler"),
    ("excitement", "Excitement — Citrus Spark"),
    ("calm", "Calm — Soft Meadow"),
    ("surprise", "Surprise — Crimson Twist"),
]
RECIPE_LABELS = {emo: label for emo, label in RECIPE_MENU}

# ------------------------------------------------------------
# DISPLAY SETUP
# ------------------------------------------------------------
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
spi = board.SPI()

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=None,
    baudrate=64_000_000,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)

# ------------------------------------------------------------
# ROTARY ENCODER + BUTTON
# ------------------------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
ss = seesaw.Seesaw(i2c, addr=0x36)

encoder = rotaryio.IncrementalEncoder(ss)
button = seesaw_dio.DigitalIO(ss, 24)
button.switch_to_input()

last_pos = encoder.position
last_button = button.value

# ------------------------------------------------------------
# SERIAL → ARDUINO
# ------------------------------------------------------------
ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
time.sleep(2)


def pump_run_ms(pump_index: int, ms: int):
    """Send a RUN command to the Arduino for a given pump and duration."""
    if ms < 0:
        ms = 0
    cmd = f"RUN {pump_index} {ms}\n"
    ser.write(cmd.encode())
    time.sleep(0.05)


def pump_dose(pump_index: int, ml: float):
    """Run a pump for the required time to dispense ml mL, using calibrated timing."""
    if ml <= 0:
        return
    ms = int(ml * MS_PER_ML)
    pump_run_ms(pump_index, ms)


# ------------------------------------------------------------
# MUSIC / BLUETOOTH HELPERS
# ------------------------------------------------------------
def is_bluetooth_connected():
    """
    Returns True if Bluetooth device is connected.
    If BT_DEVICE_MAC is None, we simply return True so music always plays,
    and you route audio to Bluetooth at the OS level.
    """
    if BT_DEVICE_MAC is None:
        return True
    try:
        out = subprocess.check_output(
            ["bluetoothctl", "info", BT_DEVICE_MAC],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return "Connected: yes" in out
    except Exception:
        return False


def update_music():
    """Start/stop looping lounge music based on Bluetooth connection."""
    global music_proc
    # If music file is missing, do nothing
    if not os.path.exists(MUSIC_FILE):
        return

    connected = is_bluetooth_connected()

    if connected:
        # Start music if not already playing
        if music_proc is None or music_proc.poll() is not None:
            # Loop the WAV forever using aplay in a shell loop
            cmd = f"while true; do aplay -q '{MUSIC_FILE}'; done"
            music_proc = subprocess.Popen(
                ["bash", "-lc", cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    else:
        # Stop music if currently playing
        if music_proc is not None and music_proc.poll() is None:
            music_proc.terminate()
            music_proc = None


# ------------------------------------------------------------
# BASIC TEXT RENDERING
# ------------------------------------------------------------
def wrap_text(text, width_px):
    """Simple word-wrap by width in pixels."""
    draw = ImageDraw.Draw(Image.new("RGB", (W, H)))
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = f"{cur} {w}" if cur else w
        if draw.textlength(test, font=FONT) <= width_px:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_simple_text(text):
    """Draw multi-line text full-screen, no selection, black on white."""
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    margin = 6
    y = margin
    lh = FONT.getbbox("Ay")[3] + 4
    for line in wrap_text(text, W - 2 * margin):
        d.text((margin, y), line, font=FONT, fill=(0, 0, 0))
        y += lh
    display.image(img.rotate(90, expand=True))


# ------------------------------------------------------------
# MENU STATE
# ------------------------------------------------------------
MENU = [
    "Record Mood",
    "Mix Drink",
    "Select Recipe",
    "Pump Test",
]
cursor = 0

# Pump test menu (scrollable)
in_pump_test = False
pump_cursor = 0
pump_offset = 0
PUMP_TEST_MENU = [
    "Pump 0",
    "Pump 1",
    "Pump 2",
    "Pump 3",
    "Pump 4",
    "Pump 5",
    "Cancel",
]

# Recipe select (scrollable)
in_recipe_select = False
recipe_cursor = 0       # index of selected item in full list
recipe_offset = 0       # top visible index

# Mix preview (scrollable)
in_mix_preview = False
mix_preview_lines = []
mix_preview_cursor = 0
mix_preview_offset = 0
mix_preview_emo_key = None
mix_preview_label = ""

current_emotion = None

# ------------------------------------------------------------
# MENU DRAWING
# ------------------------------------------------------------
def draw_menu():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    margin = 6
    y = margin
    lh = FONT.getbbox("Ay")[3] + 6

    # Elegant title with single-line kaomoji
    d.text((margin, y), "Welcome to MIXI", font=FONT, fill=(0, 0, 0))
    y += lh

    for i, item in enumerate(MENU):
        y0, y1 = y, y + lh
        if i == cursor:
            d.rectangle([0, y0, W, y1], fill=(0, 0, 0))
            d.text((margin, y0 + 2), item, font=FONT, fill=(255, 255, 255))
        else:
            d.text((margin, y0 + 2), item, font=FONT, fill=(0, 0, 0))
        y += lh

    display.image(img.rotate(90, expand=True))


def draw_pump_test_menu():
    """Scrollable pump test menu with Cancel."""
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    labels = PUMP_TEST_MENU
    total_items = len(labels)

    margin = 6
    y = margin
    lh = FONT.getbbox("Ay")[3] + 6

    d.text((margin, y), "Pump Test", font=FONT, fill=(0, 0, 0))
    y += lh

    max_rows = max(1, (H - y - margin) // lh)

    start = pump_offset
    end = min(start + max_rows, total_items)

    for idx in range(start, end):
        item = labels[idx]
        y0, y1 = y, y + lh
        if idx == pump_cursor:
            d.rectangle([0, y0, W, y1], fill=(0, 0, 0))
            d.text((margin, y0 + 2), item, font=FONT, fill=(255, 255, 255))
        else:
            d.text((margin, y0 + 2), item, font=FONT, fill=(0, 0, 0))
        y += lh

    display.image(img.rotate(90, expand=True))


def draw_recipe_menu():
    """Scrollable recipe selection menu using recipe_cursor + recipe_offset."""
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    labels = [label for (_, label) in RECIPE_MENU] + ["Cancel"]
    total_items = len(labels)

    margin = 6
    y = margin
    lh = FONT.getbbox("Ay")[3] + 6

    # Title
    d.text((margin, y), "Select Recipe", font=FONT, fill=(0, 0, 0))
    y += lh

    # Visible rows
    max_rows = max(1, (H - y - margin) // lh)

    start = recipe_offset
    end = min(start + max_rows, total_items)

    for idx in range(start, end):
        item = labels[idx]
        y0, y1 = y, y + lh
        if idx == recipe_cursor:
            d.rectangle([0, y0, W, y1], fill=(0, 0, 0))
            d.text((margin, y0 + 2), item, font=FONT, fill=(255, 255, 255))
        else:
            d.text((margin, y0 + 2), item, font=FONT, fill=(0, 0, 0))
        y += lh

    display.image(img.rotate(90, expand=True))


def draw_mix_preview():
    """Scrollable mix preview with Continue/Cancel at bottom."""
    global mix_preview_offset

    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    margin = 6
    y = margin
    lh = FONT.getbbox("Ay")[3] + 6

    max_rows = max(1, (H - 2 * margin) // lh)

    # Adjust offset so selected stays visible
    if mix_preview_cursor < mix_preview_offset:
        mix_preview_offset = mix_preview_cursor
    elif mix_preview_cursor >= mix_preview_offset + max_rows:
        mix_preview_offset = mix_preview_cursor - max_rows + 1

    start = mix_preview_offset
    end = min(start + max_rows, len(mix_preview_lines))

    for idx in range(start, end):
        line = mix_preview_lines[idx]
        y0, y1 = y, y + lh
        if idx == mix_preview_cursor:
            d.rectangle([0, y0, W, y1], fill=(0, 0, 0))
            d.text((margin, y0 + 2), line, font=FONT, fill=(255, 255, 255))
        else:
            d.text((margin, y0 + 2), line, font=FONT, fill=(0, 0, 0))
        y += lh

    display.image(img.rotate(90, expand=True))


# ------------------------------------------------------------
# RECIPE HELPERS
# ------------------------------------------------------------
def get_recipe_by_emotion(emo_key):
    """Return (name, description, ml_list) for an emotion key, or None."""
    if emo_key not in RECIPES:
        return None
    data = RECIPES[emo_key]
    name = data.get("name", emo_key.title())
    desc = data.get("description", "")
    ml = data.get("ml", [])
    ml = (ml + [0] * len(INGREDIENTS))[: len(INGREDIENTS)]
    return name, desc, ml


def scale_ml_to_target(ml_list, target_ml=FIVE_OZ_ML):
    """Scale ml_list so that sum(ml_list) == target_ml, preserving proportions."""
    total = sum(ml_list)
    if total <= 0:
        return [0] * len(ml_list)
    scale = target_ml / total
    return [m * scale for m in ml_list]


def build_mix_preview_lines(emo_key, label_for_display=None):
    """Build the list of lines shown in the Mix Drink preview screen."""
    rec = get_recipe_by_emotion(emo_key)
    if not rec:
        return ["No recipe found", "Cancel"]

    name, desc, ml_list = rec
    scaled = scale_ml_to_target(ml_list, FIVE_OZ_ML)

    label = label_for_display if label_for_display else name
    lines = []

    # Header
    lines.append(label)
    lines.append(f"({emo_key})")
    lines.append("")

    # Description
    if desc:
        lines.extend(wrap_text(desc, W - 12))
        lines.append("")

    # Ingredients
    total_ml = int(round(sum(scaled)))
    lines.append(f"Ingredients (total {total_ml} mL):")
    for i, ml in enumerate(scaled):
        if ml <= 0:
            continue
        amt = int(round(ml))
        lines.append(f"- {INGREDIENTS[i]}: {amt} mL")
    lines.append("")

    # Actions
    lines.append("Continue")
    lines.append("Cancel")

    return lines


def run_scaled_recipe_from_emotion(emo_key, label_for_display=None):
    """Fetch ml array for emotion, scale to 148 mL, and dispense."""
    rec = get_recipe_by_emotion(emo_key)
    if not rec:
        draw_simple_text("No recipe for:\n" + emo_key)
        time.sleep(1)
        return
    name, desc, ml_list = rec
    scaled = scale_ml_to_target(ml_list, FIVE_OZ_ML)

    title = label_for_display if label_for_display else name
    draw_simple_text(f"Mixing:\n{title}")

    for i, ml in enumerate(scaled):
        if ml > 0:
            pump_dose(i, ml)
            time.sleep(0.2)

    draw_simple_text("Drink Ready!")
    time.sleep(1)


# ------------------------------------------------------------
# SPEECH + SENTIMENT
# ------------------------------------------------------------
recognizer = sr.Recognizer()
audio_buffer = []
recording = False
stream = None


def audio_callback(indata, frames, time_info, status):
    audio_buffer.append(indata.copy())


def start_recording():
    global audio_buffer
    audio_buffer = []
    draw_simple_text("Recording...")
    return sd.InputStream(
        samplerate=16000,
        channels=1,
        dtype="int16",
        callback=audio_callback,
    )


def stop_and_transcribe():
    if not audio_buffer:
        return ""
    draw_simple_text("Processing...")
    audio = np.concatenate(audio_buffer)
    audio_obj = sr.AudioData(audio.tobytes(), 16000, 2)
    try:
        text = recognizer.recognize_google(audio_obj)
        return text
    except Exception:
        return ""


def classify_sentiment(text: str) -> str:
    """
    Ask the model to return exactly one of the allowed emotion labels.
    This avoids the 'always calm' fallback caused by parsing the first word
    of a full sentence.
    """
    allowed = ", ".join(EMOTIONS)
    prompt = (
        "You are an emotion classifier.\n"
        f"Return ONLY one word (no punctuation): one of {allowed}.\n"
        "Classify the dominant emotion of this text:\n\n"
        f"\"{text}\""
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3,
            temperature=0,
        )
        label = resp.choices[0].message.content.strip().lower()

        # Simple synonym mapping for robustness
        synonyms = {
            "happy": "happiness",
            "joy": "happiness",
            "joyful": "happiness",
            "sad": "sadness",
            "unhappy": "sadness",
            "depressed": "sadness",
            "upset": "sadness",
            "angry": "stress",
            "anger": "stress",
            "mad": "stress",
            "stressed": "stress",
            "anxious": "stress",
            "excited": "excitement",
            "thrilled": "excitement",
            "relaxed": "calm",
            "chill": "calm",
            "peaceful": "calm",
            "surprised": "surprise",
            "shocked": "surprise",
        }

        if label in synonyms:
            label = synonyms[label]

        if label not in EMOTIONS:
            label = "calm"

        return label
    except Exception:
        return "calm"


# ------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------
draw_menu()

while True:
    # Update background music based on Bluetooth status
    update_music()

    pos = encoder.position
    diff = pos - last_pos

    # Rotary movement
    if diff:
        if in_pump_test:
            labels = PUMP_TEST_MENU
            total_items = len(labels)
            pump_cursor = (pump_cursor + diff) % total_items

            margin = 6
            lh = FONT.getbbox("Ay")[3] + 6
            title_height = margin + lh
            max_rows = max(1, (H - title_height - margin) // lh)

            if pump_cursor < pump_offset:
                pump_offset = pump_cursor
            elif pump_cursor >= pump_offset + max_rows:
                pump_offset = pump_cursor - max_rows + 1

            draw_pump_test_menu()

        elif in_recipe_select:
            # scroll within recipe list
            labels = [label for (_, label) in RECIPE_MENU] + ["Cancel"]
            total_items = len(labels)
            recipe_cursor = (recipe_cursor + diff) % total_items

            # Compute visible rows
            margin = 6
            lh = FONT.getbbox("Ay")[3] + 6
            title_height = margin + lh
            max_rows = max(1, (H - title_height - margin) // lh)

            if recipe_cursor < recipe_offset:
                recipe_offset = recipe_cursor
            elif recipe_cursor >= recipe_offset + max_rows:
                recipe_offset = recipe_cursor - max_rows + 1

            draw_recipe_menu()

        elif in_mix_preview:
            mix_preview_cursor = (mix_preview_cursor + diff) % len(mix_preview_lines)
            draw_mix_preview()

        else:
            cursor = (cursor + diff) % len(MENU)
            draw_menu()

    last_pos = pos

    # Button press
    if button.value == False and last_button == True:
        time.sleep(0.15)

        # ------------------------------
        # PUMP TEST MODE
        # ------------------------------
        if in_pump_test:
            sel = PUMP_TEST_MENU[pump_cursor]
            if sel.startswith("Pump"):
                p = int(sel.split()[1])
                draw_simple_text(f"Running Pump {p}")
                pump_run_ms(p, 5000)  # 5 seconds
                time.sleep(1)
                draw_pump_test_menu()
            elif sel == "Cancel":
                in_pump_test = False
                draw_menu()

        # ------------------------------
        # MIX PREVIEW MODE
        # ------------------------------
        elif in_mix_preview:
            choice = mix_preview_lines[mix_preview_cursor].strip().lower()
            if choice == "continue":
                run_scaled_recipe_from_emotion(mix_preview_emo_key, mix_preview_label)
                in_mix_preview = False
                draw_menu()
            elif choice == "cancel":
                in_mix_preview = False
                draw_menu()
            # else: clicking on other lines does nothing

        # ------------------------------
        # RECIPE SELECT MODE (manual)
        # ------------------------------
        elif in_recipe_select:
            labels = [label for (_, label) in RECIPE_MENU] + ["Cancel"]
            choice_label = labels[recipe_cursor]

            if choice_label == "Cancel":
                in_recipe_select = False
                draw_menu()
            else:
                emo_key = RECIPE_MENU[recipe_cursor][0]
                run_scaled_recipe_from_emotion(emo_key, choice_label)
                in_recipe_select = False
                draw_menu()

        # ------------------------------
        # MAIN MENU
        # ------------------------------
        else:
            sel = MENU[cursor]

            # Record Mood
            if sel == "Record Mood":
                if not recording:
                    recording = True
                    stream = start_recording()
                    stream.start()
                else:
                    recording = False
                    if stream:
                        stream.stop()
                        stream.close()
                        stream = None

                    text = stop_and_transcribe()

                    if text:
                        # 1) Show the recognized speech first
                        draw_simple_text(text)
                        time.sleep(2.5)

                        # 2) Then classify emotion
                        emo = classify_sentiment(text)
                        current_emotion = emo

                        # 3) Show the emotion
                        draw_simple_text(f"You feel:\n{emo}")
                        time.sleep(2.0)
                    else:
                        draw_simple_text("No transcript")
                        time.sleep(1.5)

                    draw_menu()

            # Mix Drink (AI → recipe with preview)
            elif sel == "Mix Drink":
                if not current_emotion:
                    draw_simple_text("Record mood first")
                    time.sleep(1.5)
                    draw_menu()
                else:
                    # Build preview lines for the emotion recipe
                    label = RECIPE_LABELS.get(current_emotion, current_emotion.title())
                    mix_preview_lines = build_mix_preview_lines(current_emotion, label)
                    mix_preview_emo_key = current_emotion
                    mix_preview_label = label
                    # default selection: "Continue" (second to last line)
                    mix_preview_cursor = max(0, len(mix_preview_lines) - 2)
                    mix_preview_offset = 0
                    in_mix_preview = True
                    draw_mix_preview()

            # Manual Select Recipe
            elif sel == "Select Recipe":
                in_recipe_select = True
                recipe_cursor = 0
                recipe_offset = 0
                draw_recipe_menu()

            # Pump Test
            elif sel == "Pump Test":
                in_pump_test = True
                pump_cursor = 0
                pump_offset = 0
                draw_pump_test_menu()

    last_button = button.value
    time.sleep(0.01)
