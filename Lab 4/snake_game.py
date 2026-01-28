# Portions of this code were generated with the help of OpenAI's ChatGPT.
# Reviewed and adapted for Interactive Device Design, 2025.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
import turtle

# ---------- (Optional) Joystick ----------
try:
    import qwiic_joystick
    HAS_JOYSTICK = True
except Exception:
    HAS_JOYSTICK = False


class JoystickReader:
    def __init__(self, deadzone=150, center=512):
        self.deadzone = deadzone
        self.center = center
        self.joy = None
        self.ok = False
        if HAS_JOYSTICK:
            try:
                self.joy = qwiic_joystick.QwiicJoystick()
                if self.joy.connected:
                    self.joy.begin()
                    self.ok = True
                    print(f"[Joystick] connected (FW {self.joy.version})")
                else:
                    print("[Joystick] not detected; using keyboard only.")
            except Exception as e:
                print(f"[Joystick] init failed: {e}")
        else:
            print("[Joystick] library not found; using keyboard only.")

    def read_dir(self):
        if not self.ok:
            return None
        try:
            x = self.joy.horizontal
            y = self.joy.vertical
            dx = x - self.center
            dy = y - self.center
            if abs(dx) < self.deadzone and abs(dy) < self.deadzone:
                return None
            if abs(dx) > abs(dy):
                return "left" if dx > 0 else "right"
            else:
                return "up" if dy > 0 else "down"
        except:
            return None


# ---------- (Optional IMU) ----------
try:
    import board, busio
    from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
    HAS_IMU = True
except Exception:
    HAS_IMU = False


class IMUShakeEvent:
    THRESH = 3.2
    DEBOUNCE = 0.20

    def __init__(self):
        self.ok = False
        self._last_fire = 0.0
        if HAS_IMU:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.imu = LSM6DS3(i2c, address=0x6A)
                self.ok = True
                print("[IMU] ready for shake events")
            except Exception as e:
                print(f"[IMU] init failed: {e}")
        else:
            print("[IMU] not available; shake disabled")

    def _gyro_mag(self):
        if not self.ok:
            return 0.0
        gx, gy, gz = self.imu.gyro
        return (gx*gx + gy*gy + gz*gz)**0.5

    def shake_event(self):
        if not self.ok:
            return False
        g = self._gyro_mag()
        now = time.monotonic()
        if g > self.THRESH and (now - self._last_fire) >= self.DEBOUNCE:
            self._last_fire = now
            return True
        return False


# ---------- Game setup ----------
wn = turtle.Screen()
wn.setup(600, 600)
wn.bgcolor("black")
wn.title("Snake (Shake-to-Eat)")
wn.tracer(0)

head = turtle.Turtle()
head.speed(0)
head.shape("square")
head.color("green")
head.penup()
head.goto(0, 0)
head.direction = "stop"

food = turtle.Turtle()
food.speed(0)
food.shape("square")
food.color("white")      # always white
food.penup()
food.goto(0, 100)

segments = []
score = 0
high_score = 0

pen = turtle.Turtle()
pen.speed(0)
pen.color("white")
pen.penup()
pen.hideturtle()
pen.goto(0, 260)
pen.write("Score: 0  High Score: 0",
          align="center", font=("Courier", 24, "normal"))


# Movement functions (fixed)
def go_up():
    if head.direction != "down":
        head.direction = "up"

def go_down():
    if head.direction != "up":
        head.direction = "down"

def go_left():
    if head.direction != "right":
        head.direction = "left"

def go_right():
    if head.direction != "left":
        head.direction = "right"


def move():
    if head.direction == "up":
        head.sety(head.ycor()+20)
    elif head.direction == "down":
        head.sety(head.ycor()-20)
    elif head.direction == "left":
        head.setx(head.xcor()-20)
    elif head.direction == "right":
        head.setx(head.xcor()+20)


wn.listen()
wn.onkeypress(go_up, "Up")
wn.onkeypress(go_down, "Down")
wn.onkeypress(go_left, "Left")
wn.onkeypress(go_right, "Right")

joystick = JoystickReader()
imu = IMUShakeEvent()
TICK = 100


def reset_game():
    global score, segments, high_score
    time.sleep(0.2)
    head.goto(0, 0)
    head.direction = "stop"
    for s in segments:
        s.goto(1000, 1000)
    segments.clear()
    score = 0
    food.goto(random.randint(-280, 280), random.randint(-280, 280))
    pen.clear()
    pen.write(f"Score: {score}  High Score: {high_score}",
              align="center", font=("Courier", 24, "normal"))


def place_food_not_on_snake():
    for _ in range(200):
        x = random.randrange(-280, 281, 20)
        y = random.randrange(-280, 281, 20)
        if head.distance(x, y) < 20:
            continue
        bad = False
        for s in segments:
            if s.distance(x, y) < 20:
                bad = True
                break
        if not bad:
            food.goto(x, y)
            return
    food.goto(random.randint(-280, 280), random.randint(-280, 280))


def game_tick():
    global score, high_score

    # joystick input
    d = joystick.read_dir()
    if d == "up" and head.direction != "down":
        head.direction = "up"
    elif d == "down" and head.direction != "up":
        head.direction = "down"
    elif d == "left" and head.direction != "right":
        head.direction = "left"
    elif d == "right" and head.direction != "left":
        head.direction = "right"

    wn.update()

    # wrap edges
    if head.xcor() > 290: head.setx(-290)
    elif head.xcor() < -290: head.setx(290)
    if head.ycor() > 290: head.sety(-290)
    elif head.ycor() < -290: head.sety(290)

    # ---- eat logic ----
    overlapping = head.distance(food) < 20
    if overlapping and imu.shake_event():
        new_seg = turtle.Turtle()
        new_seg.speed(0)
        new_seg.shape("square")
        new_seg.color("lightgreen")
        new_seg.penup()
        segments.append(new_seg)

        score += 10
        if score > high_score:
            high_score = score
        pen.clear()
        pen.write(f"Score: {score}  High Score: {high_score}",
                  align="center", font=("Courier", 24, "normal"))

        place_food_not_on_snake()

    # move segments
    for i in range(len(segments)-1, 0, -1):
        segments[i].goto(segments[i-1].xcor(), segments[i-1].ycor())
    if segments:
        segments[0].goto(head.xcor(), head.ycor())

    move()

    # self-hit
    for s in segments:
        if s.distance(head) < 20:
            reset_game()
            break

    wn.ontimer(game_tick, TICK)


wn.ontimer(game_tick, TICK)
wn.mainloop()
