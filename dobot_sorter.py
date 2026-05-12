# dobot2_client.py
import json
import time
from turtle import color
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from dobot_functions import find_dobot_ports, safe_move

BROKER = "broker.hivemq.com"

# Connect to dobot 2
ports = find_dobot_ports()
dobot2 = Dobot(port=ports[1])
dobot2.connect()

print("Dobot Sorter ready")

HOME_POSITION = (209.6999969482422, 0.0, 100.0, 0.0) # given from the dobot
SENSOR_POSITION = (150, -190, 50, 65) # checked
CONVEYOR_POSITION = (230, -50, 50, 0) # checked
THROW_POSITION = (250, 100, 50, 0) # checked

SLEEP_TIME = 1.5

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "sorting other":
        print("Dobot Sorter start sorting other")

        # dobot to home position
        print("Drive to home...")
        safe_move(dobot2, HOME_POSITION)
        # dobot2.move_to(*HOME_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper opens
        print("Gripper opens...")
        dobot2.gripper.open()
        time.sleep(SLEEP_TIME)

        # dobot to color sensor position
        print("Arm to color sensor...")
        safe_move(dobot2, SENSOR_POSITION)
        # dobot2.move_to(*SENSOR_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper closes
        print("Gripper closes...")
        dobot2.gripper.close()
        time.sleep(SLEEP_TIME)
        print("Gripper closed")

        # throw block away
        print("Color is not blue, throwing...")
        safe_move(dobot2, THROW_POSITION)
        # dobot2.move_to(*THROW_POSITION)
        time.sleep(SLEEP_TIME)
        dobot2.gripper.open()
        print("Block placed throwing position")

        # gripper opens
        print("Gripper opens...")
        dobot2.gripper.open()
        print("Block placed on the conveyor belt")

        # arm back to home
        print("Drive to home...")
        safe_move(dobot2, HOME_POSITION)
        # dobot2.move_to(*HOME_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper closes
        print("Gripper closes...")
        dobot2.gripper.close()
        time.sleep(SLEEP_TIME)
        print("Gripper closed")

        # close connection
        dobot2.close()

        print("Dobot Sorter finished sorting other")

        client.publish("trackmodul_ah_SS26/dobot/sorter/status", json.dumps({
            "status": "done"
        }), qos=1)

    elif data.get("command") == "sorting blue":
        print("Dobot Sorter sorting blue")

        # dobot to home position
        print("Drive to home...")
        safe_move(dobot2, HOME_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper opens
        print("Gripper opens...")
        dobot2.gripper.open()
        time.sleep(SLEEP_TIME)

        # dobot to color sensor position
        print("Arm to color sensor...")
        safe_move(dobot2, SENSOR_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper closes
        print("Gripper closes...")
        dobot2.gripper.close()
        time.sleep(SLEEP_TIME)
        print("Gripper closed")

        # but block back on conveyor belt
        safe_move(dobot2, CONVEYOR_POSITION)
        time.sleep(SLEEP_TIME)
        dobot2.gripper.open()
        print("Block placed on the conveyor belt")

        # gripper opens
        print("Gripper opens...")
        dobot2.gripper.open()
        print("Block placed on the conveyor belt")

        # arm back to home
        print("Drive to home...")
        safe_move(dobot2, HOME_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper closes
        print("Gripper closes...")
        dobot2.gripper.close()
        time.sleep(SLEEP_TIME)
        print("Gripper closed")

        # close connection
        dobot2.close()

        print("Dobot Sorter finished sorting other")

        client.publish("trackmodul_ah_SS26/dobot/sorter/status", json.dumps({
            "status": "done"
        }), qos=1)

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("trackmodul_ah_SS26/dobot/sorter/command")

client.loop_forever()
