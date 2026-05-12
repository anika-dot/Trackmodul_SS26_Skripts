import json
import time
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from dobot_functions import find_dobot_ports, safe_move

BROKER = "broker.hivemq.com"

# Connect to dobot 1
ports = find_dobot_ports()
dobot1 = Dobot(port=ports[0])
dobot1.connect()

print("Dobot Pick & Place ready")

HOME_POSITION = (209.6999969482422, 0.0, 100.0, 0.0) # given from the dobot
PICK_POSITION = (230, 85, 30, 55) #checked
SENSOR_POSITION = (150, 255, 50, 45) #checked

SLEEP_TIME = 1

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "start":
        print("Dobot Pick & Place start task")

        # dobot to home position
        print("Drive to home...")
        safe_move(dobot1, HOME_POSITION)
        time.sleep(SLEEP_TIME)

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
        time.sleep(SLEEP_TIME)

        # arm drives to object
        print("Drive to object...")
        safe_move(dobot1, PICK_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper closes
        print("Gripper closes...")
        dobot1.gripper.close()
        time.sleep(SLEEP_TIME)
        print("Gripper closed")

        # put block on color sensor
        print("Arm lifts up...")
        safe_move(dobot1, SENSOR_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper opens
        print("Gripper opens...")
        dobot1.gripper.open()
        time.sleep(SLEEP_TIME)

        # arm back to home
        print("Drive to home...")
        safe_move(dobot1, HOME_POSITION)
        time.sleep(SLEEP_TIME)

        # gripper closes
        print("Gripper closes...")
        dobot1.gripper.close()
        time.sleep(SLEEP_TIME)
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