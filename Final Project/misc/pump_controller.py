import serial
import time

# Adjust depending on your Arduino port
# Common names:
#   /dev/ttyACM0
#   /dev/ttyUSB0
#   /dev/ttyAMA0
#   /dev/ttyACM1  
SERIAL_PORT = "/dev/ttyACM0"

ser = serial.Serial(SERIAL_PORT, 9600, timeout=1)
time.sleep(2)  # give Arduino time to reset


def pump(index, duration_ms):
    """
    Run pump `index` for `duration_ms` milliseconds.
    index: 0–5
    """
    cmd = f"RUN {index} {duration_ms}\n"
    ser.write(cmd.encode('utf-8'))
    time.sleep(duration_ms / 1000 + 0.1)


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    print("Running pump #2 for 1 second")
    pump(2, 1000)

    print("Done!")
