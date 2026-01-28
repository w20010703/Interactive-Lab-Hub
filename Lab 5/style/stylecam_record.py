import os
import time
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from tflite_runtime.interpreter import Interpreter
import board, digitalio
import adafruit_rgb_display.st7789 as st7789

# --- Display setup ---
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
spi = board.SPI()
BAUDRATE = 64_000_000

disp = st7789.ST7789(
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
backlight.switch_to_output()
backlight.value = True

SCREEN_W, SCREEN_H = 240, 135
ROTATION = 90

# --- Button setup ---
button_left = digitalio.DigitalInOut(board.D23)
button_left.direction = digitalio.Direction.INPUT
button_left.pull = digitalio.Pull.UP

button_right = digitalio.DigitalInOut(board.D24)
button_right.direction = digitalio.Direction.INPUT
button_right.pull = digitalio.Pull.UP

# --- TFLite interpreters ---
style_predict = Interpreter("style_predict_fast.tflite", num_threads=4)
style_predict.allocate_tensors()

style_transform = Interpreter("style_transform_fast.tflite", num_threads=4)
style_transform.allocate_tensors()

# --- Load styles ---
style_image_paths = sorted(Path("styles").glob("*.jpg")) + sorted(Path("styles").glob("*.png"))
style_image_paths = [str(p) for p in style_image_paths]
if not style_image_paths:
    raise RuntimeError("No style images found in /styles folder.")

class StyleManager:
    def __init__(self, paths):
        self.paths = paths
        self.index = 0
    def current(self):
        return self.paths[self.index]
    def next(self):
        self.index = (self.index + 1) % len(self.paths)
        return self.current()
    def previous(self):
        self.index = (self.index - 1 + len(self.paths)) % len(self.paths)
        return self.current()

style_manager = StyleManager(style_image_paths)

def load_style_bottleneck(path):
    img = Image.open(path).convert("RGB").resize((256, 256), Image.BILINEAR)
    arr = (np.asarray(img, dtype=np.float32) / 255.0)[None, ...]
    in_idx = style_predict.get_input_details()[0]['index']
    out_idx = style_predict.get_output_details()[0]['index']
    style_predict.set_tensor(in_idx, arr)
    style_predict.invoke()
    return style_predict.get_tensor(out_idx).reshape((1,1,1,100))

def find_transform_io_and_shape(interp):
    id_content = None
    id_style = None
    content_hw = None
    for d in interp.get_input_details():
        shape = d['shape']
        dtype = d['dtype']
        idx = d['index']
        if len(shape) == 4 and shape[-1] == 3 and dtype == np.float32:
            id_content = idx
            _, H, W, _ = shape
            content_hw = (int(H), int(W))
        elif dtype == np.float32 and ((len(shape) == 2 and shape[-1] == 100) or
                                      (len(shape) == 4 and shape[-1] == 100 and shape[1] == 1 and shape[2] == 1)):
            id_style = idx
    if id_content is None or id_style is None:
        raise RuntimeError("Could not determine content/style input indices.")
    out_idx = interp.get_output_details()[0]['index']
    return id_content, id_style, out_idx, content_hw

id_c, id_s, out_idx, (CONTENT_H, CONTENT_W) = find_transform_io_and_shape(style_transform)

def preprocess_content_stretched(frame_bgr):
    resized = cv2.resize(frame_bgr, (CONTENT_W, CONTENT_H), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    rgb = rgb.astype(np.float32) / 255.0
    return rgb[None, ...]

def to_pitft_image(rgb_float01):
    arr = np.clip(rgb_float01 * 255.0, 0, 255).astype(np.uint8)
    image = Image.fromarray(arr)
    if image.size != (SCREEN_W, SCREEN_H):
        image = image.resize((SCREEN_W, SCREEN_H), Image.BILINEAR)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image = image.transpose(Image.FLIP_LEFT_RIGHT)
    return image

# --- Camera setup ---
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not cam.isOpened():
    raise RuntimeError("No webcam detected at index 0.")

# --- QuickTime .MOV writer ---
output_file = "output_stylized.mov"

# Try H.264 first, fallback to MPEG-4
fourcc = cv2.VideoWriter_fourcc(*"avc1")
video_writer = cv2.VideoWriter(output_file, fourcc, 20.0, (SCREEN_W, SCREEN_H))
if not video_writer.isOpened():
    print("H.264 not supported-using MPEG-4 fallback")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(output_file, fourcc, 20.0, (SCREEN_W, SCREEN_H))

if video_writer.isOpened():
    print(f"Recording stylized output to {output_file}")
else:
    print("Failed to initialize video writer. Check FFmpeg installation.")

# --- Run style transfer loop ---
style_bottleneck = load_style_bottleneck(style_manager.current())
print(f"Initial style: {os.path.basename(style_manager.current())}")
print("Running FAST version with style_transform_fast.tflite")

try:
    last_button_time = 0
    DEBOUNCE = 0.25
    fps_timer = time.time()
    frames = 0

    while True:
        now = time.monotonic()

        if not button_left.value and (now - last_button_time) > DEBOUNCE:
            path = style_manager.previous()
            style_bottleneck = load_style_bottleneck(path)
            print(f"Style: {os.path.basename(path)}")
            last_button_time = now

        if not button_right.value and (now - last_button_time) > DEBOUNCE:
            path = style_manager.next()
            style_bottleneck = load_style_bottleneck(path)
            print(f"Style: {os.path.basename(path)}")
            last_button_time = now

        ok, frame = cam.read()
        if not ok:
            continue

        content_input = preprocess_content_stretched(frame)
        style_transform.set_tensor(id_c, content_input)
        style_transform.set_tensor(id_s, style_bottleneck)
        style_transform.invoke()

        stylized = style_transform.get_tensor(out_idx)[0]
        pitft_img = to_pitft_image(stylized)
        disp.image(pitft_img, ROTATION)

        # --- Write video frame ---
        bgr_frame = cv2.cvtColor(np.array(pitft_img), cv2.COLOR_RGB2BGR)
        video_writer.write(bgr_frame)

        frames += 1
        if frames % 10 == 0:
            now_time = time.time()
            fps = 10 / (now_time - fps_timer)
            fps_timer = now_time

except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    cam.release()
    video_writer.release()
    print(f"Video saved as {output_file}")
