import json
import time
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from dobot_functions import find_dobot_ports

BROKER = "broker.hivemq.com"

# Connect to dobot 1
ports = find_dobot_ports()
dobot1 = Dobot(port=ports[0])
dobot1.connect()

print("Dobot Pick & Place ready")


def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "start":
        print("Dobot Pick & Place start task")

        home_position = (185.0, 100.0, 118.0, 90) #(225.0, -25.0, 100.0, 22.0)
        pick_position = (186.42, 152.0, 29.169, 90) #(200.28, 119.57, 20.38, 38.43)
        sensor_position = (19.272, 233.825, 46.538, 90) #(43.84, 222.58, 43.59, 86.45) 

        # dobot to home position
        print("Drive to home...")
        dobot1.move_to(*home_position)
        time.sleep(1)

        # start conveyor belt
        dobot1.ir_toggle(enable=True)
        print("Conveyor belt running")
        dobot1.conveyor_belt.move(speed=0.5)

        # wait until object is detected
        while dobot1.get_ir() == False:
            time.sleep(0.1)

        print("Object detected - STOP")
        dobot1.conveyor_belt.idle()

        # gripper opens
        print("Gripper opens...")
        dobot1.gripper.open()
        time.sleep(0.3)

        # arm drives to object
        print("Drive to object...")
        dobot1.move_to(*pick_position)
        time.sleep(0.3)
 
        # gripper closes
        print("Gripper closes...")
        dobot1.gripper.close()
        time.sleep(0.3)
        print("Gripper closed")

        # put block on color sensor
        print("Arm lifts up...")
        dobot1.move_to(*sensor_position)
        time.sleep(0.3)

        # gripper opens
        print("Gripper opens...")
        dobot1.gripper.open()
        time.sleep(0.3)

        # arm back to home
        print("Drive to home...")
        dobot1.move_to(*home_position)
        time.sleep(1)

        # gripper closes
        print("Gripper closes...")
        dobot1.gripper.close()
        time.sleep(1)
        print("Gripper closed")

        # close connection
        dobot1.close()
        print("Fertig")

        print("Dobot 1 finished task")

        client.publish("trackmodul_ah_SS26/dobot/pickplace/status", json.dumps({
            "status": "done"
        }), qos=1)

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("trackmodul_ah_SS26/dobot/pickplace/command")

client.loop_forever()