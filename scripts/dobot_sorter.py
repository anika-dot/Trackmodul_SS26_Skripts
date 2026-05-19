'''
This module contains all process information for Dobot "Sorter"
'''

import json
import time
from turtle import color
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from helper_functions.dobot_functions import find_dobot_ports, safe_move
from helper_functions.event_logger import EventLogger

BROKER = "broker.hivemq.com"
log = EventLogger("sorter")

# Connect to dobot 2
ports = find_dobot_ports()
dobot2 = Dobot(port=ports[1])
dobot2.connect()
log.info("dobot_connected", port=ports[1])

HOME_POSITION = (209.6999969482422, 0.0, 100.0, 0.0)
SENSOR_POSITION = (150, -190, 50, 65)
CONVEYOR_POSITION = (230, -50, 50, 0)
THROW_POSITION = (250, 100, 50, 0)

SLEEP_TIME = 1.5

def on_message(client, userdata, msg):
    '''
    Function to define the process for the dobot sorter. 
    2 options, depending on the feedback of the color sensor (blue or other color)
    '''
    data = json.loads(msg.payload.decode())

    if data.get("command") == "sorting other":
        log.info("sorter_start", command="other color")

        # dobot to home position
        with log.timed("move_to_home_initial"):
            safe_move(dobot2, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper opens
        with log.timed("gripper_open"):
            dobot2.gripper.open()
            time.sleep(SLEEP_TIME)

        # dobot to color sensor position
        with log.timed("move_to_color_sensor"):
            safe_move(dobot2, SENSOR_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper closes
        with log.timed("gripper_close"):
            dobot2.gripper.close()
            time.sleep(SLEEP_TIME)

        # throw block away
        with log.timed("throwing_block"):
            safe_move(dobot2, THROW_POSITION)
            time.sleep(SLEEP_TIME)
            dobot2.gripper.open()
        
        # gripper closes
        with log.timed("gripper_close"):
            dobot2.gripper.close()
            time.sleep(SLEEP_TIME)

        # arm back to home
        with log.timed("move_to_home_final"):
            safe_move(dobot2, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # finish sorter
        log.info("sorter_finished", command="other color")

        client.publish("trackmodul_ah_SS26/dobot/sorter/status", json.dumps({
            "status": "done"
        }), qos=1)

    elif data.get("command") == "sorting blue":
        log.info("sorter_start", command="blue")

        # dobot to home position
        with log.timed("move_to_home_initial"):
            safe_move(dobot2, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper opens
        with log.timed("gripper_open"):
            dobot2.gripper.open()
            time.sleep(SLEEP_TIME)

        # dobot to color sensor position
        with log.timed("move_to_color_sensor"):
            safe_move(dobot2, SENSOR_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper closes
        with log.timed("gripper_close"):
            dobot2.gripper.close()
            time.sleep(SLEEP_TIME)

        # put block back on conveyor belt
        with log.timed("move_to_conveyor"):
            safe_move(dobot2, CONVEYOR_POSITION)
            time.sleep(SLEEP_TIME)
            dobot2.gripper.open()

        # gripper closes
        with log.timed("gripper_close"):
            dobot2.gripper.close()
            time.sleep(SLEEP_TIME)

        # arm back to home
        with log.timed("move_to_home_final"):
            safe_move(dobot2, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # finish sorter
        log.info("sorter_finished", command="blue")

        client.publish("trackmodul_ah_SS26/dobot/sorter/status", json.dumps({
            "status": "done"
        }), qos=1)

def cleanup():
    '''
    Function to close connection manually
    '''
    dobot2.close()
    print("Dobot connection closed")

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("trackmodul_ah_SS26/dobot/sorter/command")

# loop until user interrupts manually
try:
    client.loop_forever()
except KeyboardInterrupt:
    cleanup()
    client.disconnect()