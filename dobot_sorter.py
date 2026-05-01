# dobot2_client.py
import json
import time
from turtle import color
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from dobot_functions import find_dobot_ports
from event_logger import EventLogger

BROKER = "broker.hivemq.com"
log = EventLogger("sorter")

# Connect to dobot 2
ports = find_dobot_ports()
dobot2 = Dobot(port=ports[0])
dobot2.connect()
log.info("dobot_connected", port=ports[0])
print("Dobot Sorter ready") # To Do: Delete print statement

home_position = (154.84, 25.89, 38.79, 18.44) #(154.84, 25.89, 38.79, 18.44) #(225.0, -25.0, 100.0, 22.0)
sensor_position = (150.0, 45.0, 45.0, 40.0) #(148.35, -25.89, 38.79, 18.44) #(200.0, 200.0, 80.0, 25.0)
conveyor_position = (233.91, -13.74, 39.27, 24.97)
throw_position = (316.00, 8.91, 43.16, 29.95)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "sorting other":
        print("Dobot Sorter start sorting other")
        log.info("sorter_start", command="other color")

        # dobot to home position
        with log.timed("move_to_home_initial"):
            print("Drive to home...") # To Do: Delete print statement
            dobot2.move_to(*home_position)
            time.sleep(0.3)

        # gripper opens
        with log.timed("gripper_open"):
            print("Gripper opens...") # To Do: Delete print statement
            dobot2.gripper.open()
            time.sleep(0.3)

        # dobot to color sensor position
        with log.timed("move_to_color_sensor"):
            print("Arm to color sensor...") # To Do: Delete print statement
            dobot2.move_to(*sensor_position)
            time.sleep(0.3)

        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot2.gripper.close()
            time.sleep(0.3)
            print("Gripper closed") # To Do: Delete print statement

        # throw block away
        with log.timed("throwing_block"):
            print("Color is not blue, throwing...") # To Do: Delete print statement
            dobot2.move_to(*throw_position)
            time.sleep(0.3)
            dobot2.gripper.open()
            print("Block placed throwing position") # To Do: Delete print statement
        
        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot2.gripper.close()
            time.sleep(0.3)
            print("Gripper closed") # To Do: Delete print statement

        # arm back to home
        with log.timed("move_to_home_final"):
            print("Drive to home...") # To Do: Delete print statement
            dobot2.move_to(*home_position)
            time.sleep(0.3)

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
            dobot2.move_to(*home_position)
            time.sleep(0.3)

        # gripper opens
        with log.timed("gripper_open"):
            print("Gripper opens...") # To Do: Delete print statement
            dobot2.gripper.open()
            time.sleep(0.3)

        # dobot to color sensor position
        with log.timed("move_to_color_sensor"):
            print("Arm to color sensor...") # To Do: Delete print statement
            dobot2.move_to(*sensor_position)
            time.sleep(0.3)

        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot2.gripper.close()
            time.sleep(0.3)
            print("Gripper closed") # To Do: Delete print statement

        # but block back on conveyor belt
        with log.timed("move_to_conveyor"):
            dobot2.move_to(*conveyor_position)
            time.sleep(0.3)
            dobot2.gripper.open()
            print("Block placed on the conveyor belt") # To Do: Delete print statement

        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot2.gripper.close()
            time.sleep(0.3)
            print("Gripper closed") # To Do: Delete print statement

        # arm back to home
        with log.timed("move_to_home_final"):
            print("Drive to home...") # To Do: Delete print statement
            dobot2.move_to(*home_position)
            time.sleep(0.3)

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
