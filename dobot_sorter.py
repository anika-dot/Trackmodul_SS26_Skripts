# dobot2_client.py
import json
import time
from turtle import color
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from dobot_functions import find_dobot_ports, safe_move
from event_logger import EventLogger

BROKER = "broker.hivemq.com"
log = EventLogger("sorter")

# Connect to dobot 2
ports = find_dobot_ports()
dobot2 = Dobot(port=ports[1])
dobot2.connect()
log.info("dobot_connected", port=ports[0])
print("Dobot Sorter ready") # To Do: Delete print statement

HOME_POSITION = (209.6999969482422, 0.0, 100.0, 0.0) # given from the dobot
SENSOR_POSITION = (150, -190, 50, 65) # checked
CONVEYOR_POSITION = (230, -50, 50, 0) # checked
THROW_POSITION = (250, 100, 50, 0) # checked

SLEEP_TIME = 1.5

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "sorting other":
        print("Dobot Sorter start sorting other")
        log.info("sorter_start", command="other color")

        # dobot to home position
        with log.timed("move_to_home_initial"):
            print("Drive to home...") # To Do: Delete print statement
            safe_move(dobot2, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper opens
        with log.timed("gripper_open"):
            print("Gripper opens...") # To Do: Delete print statement
            dobot2.gripper.open()
            time.sleep(SLEEP_TIME)

        # dobot to color sensor position
        with log.timed("move_to_color_sensor"):
            print("Arm to color sensor...") # To Do: Delete print statement
            safe_move(dobot2, SENSOR_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot2.gripper.close()
            time.sleep(SLEEP_TIME)
            print("Gripper closed") # To Do: Delete print statement

        # throw block away
        with log.timed("throwing_block"):
            print("Color is not blue, throwing...") # To Do: Delete print statement
            safe_move(dobot2, THROW_POSITION)
            time.sleep(SLEEP_TIME)
            dobot2.gripper.open()
            print("Block placed throwing position") # To Do: Delete print statement
        
        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot2.gripper.close()
            time.sleep(SLEEP_TIME)
            print("Gripper closed") # To Do: Delete print statement

        # arm back to home
        with log.timed("move_to_home_final"):
            print("Drive to home...") # To Do: Delete print statement
            safe_move(dobot2, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # close connection
        dobot2.close()
        log.info("sorter_finished", command="other color")
        print("Dobot Sorter finished sorting other") # To Do: Delete print statement

        client.publish("trackmodul_ah_SS26/dobot/sorter/status", json.dumps({
            "status": "done"
        }), qos=1)

    elif data.get("command") == "sorting blue":
        print("Dobot Sorter sorting blue") # To Do: Delete print statement
        log.info("sorter_start", command="blue")

        # dobot to home position
        with log.timed("move_to_home_initial"):
            print("Drive to home...") # To Do: Delete print statement
            safe_move(dobot2, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper opens
        with log.timed("gripper_open"):
            print("Gripper opens...") # To Do: Delete print statement
            dobot2.gripper.open()
            time.sleep(SLEEP_TIME)

        # dobot to color sensor position
        with log.timed("move_to_color_sensor"):
            print("Arm to color sensor...") # To Do: Delete print statement
            safe_move(dobot2, SENSOR_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot2.gripper.close()
            time.sleep(SLEEP_TIME)
            print("Gripper closed") # To Do: Delete print statement

        # put block back on conveyor belt
        with log.timed("move_to_conveyor"):
            safe_move(dobot2, CONVEYOR_POSITION)
            time.sleep(SLEEP_TIME)
            dobot2.gripper.open()
            print("Block placed on the conveyor belt") # To Do: Delete print statement

        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot2.gripper.close()
            time.sleep(SLEEP_TIME)
            print("Gripper closed") # To Do: Delete print statement

        # arm back to home
        with log.timed("move_to_home_final"):
            print("Drive to home...") # To Do: Delete print statement
            safe_move(dobot2, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # close connection
        dobot2.close()
        log.info("sorter_finished", command="blue")
        print("Dobot Sorter finished sorting blue") # To Do: Delete print statement

        client.publish("trackmodul_ah_SS26/dobot/sorter/status", json.dumps({
            "status": "done"
        }), qos=1)

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("trackmodul_ah_SS26/dobot/sorter/command")

client.loop_forever()
