import json
import time
from turtle import color
from xml.etree.ElementTree import VERSION
from xmlrpc import client
import paho.mqtt.client as mqtt
from dobot_functions import find_dobot_ports
from pydobotplus import Dobot

BROKER = "broker.hivemq.com"

# Connect to color sensor
ports = find_dobot_ports()
color_sensor = Dobot(port=ports[0])

print("Color sensor ready")

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "scanning":
        print("Color sensor start scanning")

        VERSION = 2  # Set to 2 for Dobot Magician, 1 for Dobot M1

        color_sensor.set_color(True, VERSION)

        # Reading color sensor...
        print("Reading color sensor...")
        color_sensor.get_color()
        rgb = color_sensor.get_color()
        time.sleep(0.3)
        print("Color sensor finished scanning")

        if rgb == [False, False, True]:
            color = "blue"
        else:
            color = "other"

        client.publish("trackmodul_ah_SS26/dobot/colorsensor/status", json.dumps({
            "status": "done",
            "color": color  
        }), qos=1)

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("trackmodul_ah_SS26/dobot/colorsensor/command")

client.loop_forever()
