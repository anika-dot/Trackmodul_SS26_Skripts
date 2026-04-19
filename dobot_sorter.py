# dobot2_client.py
import json
import time
from turtle import color
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from dobot_functions import find_dobot_ports

BROKER = "172.20.10.12"

# Connect to dobot 2
ports = find_dobot_ports()
dobot2 = Dobot(port=ports[0])
dobot2.connect()

print("Dobot Sorter ready")

home_position = (154.84, 25.89, 38.79, 18.44) #(154.84, 25.89, 38.79, 18.44) #(225.0, -25.0, 100.0, 22.0)
sensor_position = (150.0, 45.0, 45.0, 40.0) #(148.35, -25.89, 38.79, 18.44) #(200.0, 200.0, 80.0, 25.0)
conveyor_position = (233.91, -13.74, 39.27, 24.97)
throw_position = (316.00, 8.91, 43.16, 29.95)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "sorting other":
        print("Dobot Sorter start sorting other")

        # dobot to home position
        print("Drive to home...")
        dobot2.move_to(*home_position)
        time.sleep(0.3)

        # gripper opens
        print("Gripper opens...")
        dobot2.gripper.open()
        time.sleep(0.3)

        # dobot to color sensor position
        print("Arm to color sensor...")
        dobot2.move_to(*sensor_position)
        time.sleep(0.3)

        # gripper closes
        print("Gripper closes...")
        dobot2.gripper.close()
        time.sleep(0.3)
        print("Gripper closed")

        # throw block away
        print("Color is not blue, throwing...")
        dobot2.move_to(*throw_position)
        time.sleep(0.3)
        dobot2.gripper.open()
        print("Block placed throwing position")

        # gripper opens
        print("Gripper opens...")
        dobot2.gripper.open()
        print("Block placed on the conveyor belt")

        # arm back to home
        print("Drive to home...")
        dobot2.move_to(*home_position)
        time.sleep(0.3)

        # gripper closes
        print("Gripper closes...")
        dobot2.gripper.close()
        time.sleep(0.3)
        print("Gripper closed")

        # close connection
        dobot2.close()

        print("Dobot Sorter finished sorting other")

        client.publish("dobot/sorter/status", json.dumps({
            "status": "done"
        }), qos=1)

    elif data.get("command") == "sorting blue":
        print("Dobot Sorter sorting blue")

        # dobot to home position
        print("Drive to home...")
        dobot2.move_to(*home_position)
        time.sleep(0.3)

        # gripper opens
        print("Gripper opens...")
        dobot2.gripper.open()
        time.sleep(0.3)

        # dobot to color sensor position
        print("Arm to color sensor...")
        dobot2.move_to(*sensor_position)
        time.sleep(0.3)

        # gripper closes
        print("Gripper closes...")
        dobot2.gripper.close()
        time.sleep(0.3)
        print("Gripper closed")

        # but block back on conveyor belt
        dobot2.move_to(*conveyor_position)
        time.sleep(0.3)
        dobot2.gripper.open()
        print("Block placed on the conveyor belt")

        # gripper opens
        print("Gripper opens...")
        dobot2.gripper.open()
        print("Block placed on the conveyor belt")

        # arm back to home
        print("Drive to home...")
        dobot2.move_to(*home_position)
        time.sleep(0.3)

        # gripper closes
        print("Gripper closes...")
        dobot2.gripper.close()
        time.sleep(0.3)
        print("Gripper closed")

        # close connection
        dobot2.close()

        print("Dobot Sorter finished sorting other")

        client.publish("dobot/sorter/status", json.dumps({
            "status": "done"
        }), qos=1)

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("dobot/sorter/command")

client.loop_forever()
