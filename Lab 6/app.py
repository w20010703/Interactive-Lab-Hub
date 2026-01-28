from flask import Flask, render_template, jsonify
from flask_mqtt import Mqtt

BROKER = "10.56.129.182"
PORT = 1883

app = Flask(__name__)
app.config["MQTT_BROKER_URL"] = BROKER
app.config["MQTT_BROKER_PORT"] = PORT
app.config["MQTT_KEEPALIVE"] = 60
mqtt = Mqtt(app)

# store cube colors
colors = {1: (0, 0, 0), 2: (0, 0, 0), 3: (0, 0, 0)}

def blend_colors(c1, c2, c3):
    return (
        int((c1[0] + c2[0] + c3[0]) / 3),
        int((c1[1] + c2[1] + c3[1]) / 3),
        int((c1[2] + c2[2] + c3[2]) / 3),
    )

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe("cube/+/emotion")
    print("Connected to MQTT broker")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        topic = message.topic
        cube_id = int(topic.split("/")[1])
        r, g, b = map(int, message.payload.decode().split(","))
        colors[cube_id] = (r, g, b)
    except Exception as e:
        print("Error parsing message:", e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/colors")
def get_colors():
    c1, c2, c3 = colors[1], colors[2], colors[3]
    blend = blend_colors(c1, c2, c3)
    return jsonify({"1": c1, "2": c2, "3": c3, "blend": blend})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
