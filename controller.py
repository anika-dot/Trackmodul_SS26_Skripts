# beide Dobots subscriber, für die Rückmeldung auch als publisher

# Server = zentrales Skript, als publisher

import time
import json
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
state = "INIT"

def on_message(client, userdata, msg):
    global state

    data = json.loads(msg.payload.decode())
    topic = msg.topic

    print(f"[RECV] {topic} -> {data}")

    if topic == "dobot/pickplace/status" and state == "WAIT_D_pickplace":
        print("Start Color Sensor")
        client.publish("dobot/colorsensor/command", json.dumps({"command": "scanning"}))
        state = "WAIT_D_color_sensor"

    elif topic == "dobot/colorsensor/status" and state == "WAIT_D_color_sensor":
        detected_color = data.get("color")

        print(f"Detected color: {detected_color}")

        if detected_color == "blue":
            print("Start Dobot Sorter: BLUE")
            client.publish("dobot/sorter/command", json.dumps({"command": "sorting blue"}))
        else:
            print("Start Dobot Sorter: OTHER")
            client.publish("dobot/sorter/command", json.dumps({"command": "sorting other"}))
        
        state = "WAIT_D_Sorter"

    elif topic == "dobot/sorter/status" and state == "WAIT_D_Sorter":
        print("Finished all tasks")
        state = "DONE"

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("dobot/+/status")

client.loop_start()

time.sleep(1)

print("Start Dobot Pick & Place")
client.publish("dobot/pickplace/command", json.dumps({"command": "start"}))
state = "WAIT_D_pickplace"

while state != "DONE":
    time.sleep(1)