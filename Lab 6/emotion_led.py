import cv2
import board
import neopixel
import time
from fer.fer import FER

# ------------------------------
# LED setup
# ------------------------------
pixel_pin = board.D18          # GPIO 18 (pin 12)
num_pixels = 7
brightness = 0.3

pixels = neopixel.NeoPixel(
    pixel_pin,
    num_pixels,
    brightness=brightness,
    auto_write=False,
    pixel_order=neopixel.GRB
)

# ------------------------------
# Emotion detector setup
# ------------------------------
detector = FER()

emotion_colors = {
    "happy": (255, 200, 0),
    "sad": (0, 0, 255),
    "angry": (255, 0, 0),
    "neutral": (255, 255, 255),
    "surprise": (0, 255, 255),
    "disgust": (0, 255, 0),
    "fear": (180, 0, 255),
}

# ------------------------------
# Helper: smooth color transition
# ------------------------------
def fade_to_color(current, target, steps=25, delay=0.04):
    for i in range(steps + 1):
        interp = tuple(int(current[j] + (target[j] - current[j]) * (i / steps)) for j in range(3))
        pixels.fill(interp)
        pixels.show()
        time.sleep(delay)
    return target

# ------------------------------
# Camera setup (low res for speed)
# ------------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("No camera found. Exiting.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Window scaling factor (2 = doubles size)
display_scale = 2

print("Emotion LED color mapping started. Press 'q' to quit.")
last_color = (0, 0, 0)
last_emotion = "none"

# ------------------------------
# Main loop
# ------------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = detector.detect_emotions(frame)

    if results:
        scores = results[0]["emotions"]
        emotion = max(scores, key=scores.get)
        score = scores[emotion]

        if emotion in emotion_colors:
            target_color = emotion_colors[emotion]
            if target_color != last_color:
                print(f"Detected: {emotion} ({score:.2f}) -> {target_color}")
                last_color = fade_to_color(last_color, target_color)
            last_emotion = emotion

        # Draw all detected faces
        for r in results:
            (x, y, w, h) = r["box"]
            e = max(r["emotions"], key=r["emotions"].get)
            s = r["emotions"][e]
            color = (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label = f"{e} ({s:.2f})"
            cv2.putText(frame, label, (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    else:
        last_emotion = "none"

    # Enlarge frame for display
    display_frame = cv2.resize(
        frame,
        (int(frame.shape[1] * display_scale), int(frame.shape[0] * display_scale)),
        interpolation=cv2.INTER_NEAREST
    )

    # Show the annotated frame
    cv2.imshow("Emotion Detection", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ------------------------------
# Cleanup
# ------------------------------
cap.release()
cv2.destroyAllWindows()
pixels.fill((0, 0, 0))
pixels.show()
print("Program ended cleanly.")
