'''
This module contains the process information for the color scanner.
'''

import json
import time
from turtle import color
from xml.etree.ElementTree import VERSION
from xmlrpc import client
import paho.mqtt.client as mqtt
from pydobotplus import Dobot
from helper_functions.dobot_functions import find_dobot_ports
from helper_functions.event_logger import EventLogger

BROKER = "broker.hivemq.com"
log = EventLogger("color_scanner")

# Connect to color sensor
ports = find_dobot_ports()
color_sensor = Dobot(port=ports[1])
log.info("color_sensor_connected", port=ports[1])

def on_message(client, userdata, msg):
    '''
    Function to define process for color scanner.
    Scans color and sends information back to the controller.
    '''
    data = json.loads(msg.payload.decode())

    if data.get("command") == "scanning":
        log.info("color_sensor_start_scanning")

        VERSION = 2  # Set to 2 for Dobot Magician, 1 for Dobot M1

        color_sensor.set_color(True, VERSION)

        # Reading color sensor
        with log.timed("color_scanning"):
            color_sensor.get_color()
            rgb = color_sensor.get_color()
            time.sleep(0.3)

        if rgb == [False, False, True]:
            color = "blue"
        else:
            color = "other"

        log.info("color_scanning_finished", color=color)
          
        
        client.publish("trackmodul_ah_SS26/dobot/colorsensor/status", json.dumps({
            "status": "done",
            "color": color  
        }), qos=1)

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("trackmodul_ah_SS26/dobot/colorsensor/command")

def cleanup():
    '''
    Function to close connection manually
    '''
    color_sensor.close()
    print("Dobot connection closed")

# loop until user interrupts manually
try:
    client.loop_forever()
except KeyboardInterrupt:
    cleanup()
    client.disconnect()
