import cv2
import board
import neopixel
import time
from fer.fer import FER
from paho.mqtt import client as mqtt_client

# ---------------- Configuration ----------------
BROKER = "10.56.129.182"   # replace with broker Pi's IP
PORT = 1883
CUBE_ID = 1                # change to 1, 2, or 3 for each Pi
TOPIC = f"cube/{CUBE_ID}/emotion"

pixel_pin = board.D18
num_pixels = 7
brightness = 0.3
pixels = neopixel.NeoPixel(
    pixel_pin,
    num_pixels,
    brightness=brightness,
    auto_write=False,
    pixel_order=neopixel.GRB
)

# ---------------- Emotion Detector ----------------
# Using mtcnn=False avoids TensorFlow graph mode errors on the Pi
detector = FER(mtcnn=False)

emotion_colors = {
    "happy": (255, 200, 0),
    "sad": (0, 0, 255),
    "angry": (255, 0, 0),
    "neutral": (255, 255, 255),
    "surprise": (0, 255, 255),
    "disgust": (0, 255, 0),
    "fear": (180, 0, 255),
}

# ---------------- MQTT Setup ----------------
client = mqtt_client.Client(f"cube_{CUBE_ID}")
client.connect(BROKER, PORT)
client.loop_start()

# ---------------- Helper Functions ----------------
def fade_to_color(current, target, steps=20, delay=0.02):
    """Smooth transition between LED colors."""
    for i in range(steps + 1):
        interp = tuple(
            int(current[j] + (target[j] - current[j]) * (i / steps))
            for j in range(3)
        )
        pixels.fill(interp)
        pixels.show()
        time.sleep(delay)
    return target

# ---------------- Camera Setup ----------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

if not cap.isOpened():
    print("No camera found. Exiting.")
    exit()

print(f"Cube {CUBE_ID} publishing to {TOPIC}")
last_color = (0, 0, 0)

# ---------------- Main Loop ----------------
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = detector.detect_emotions(frame)
        if results:
            for face in results:
                (x, y, w, h) = face["box"]
                scores = face["emotions"]
                emotion = max(scores, key=scores.get)
                color = emotion_colors.get(emotion, (255, 255, 255))

                # Draw rectangle and emotion label
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{emotion}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # LED color + MQTT publish
                if color != last_color:
                    fade_to_color(last_color, color)
                    last_color = color
                    msg = f"{color[0]},{color[1]},{color[2]}"
                    client.publish(TOPIC, msg)
                    print(f"Cube {CUBE_ID}: {emotion} -> {color}")

        # Show camera output in window
        cv2.imshow(f"Cube {CUBE_ID} Emotion View", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    cap.release()
    cv2.destroyAllWindows()
    pixels.fill((0, 0, 0))
    pixels.show()
    client.loop_stop()
    print("Stopped cleanly.")
