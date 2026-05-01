import json
import time
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from dobot_functions import find_dobot_ports
from event_logger import EventLogger

BROKER = "broker.hivemq.com"

log = EventLogger("pickplace")

# Connect to dobot 1
ports = find_dobot_ports()
dobot1 = Dobot(port=ports[1])
dobot1.connect()
log.info("dobot_connected", port=ports[1])
print("Dobot Pick & Place ready") # To Do: Delete print statement

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "start":
        print("Dobot Pick & Place start task") # To Do: Delete print statement
        log.info("task_received", command="start")

        home_position = (185.0, 100.0, 118.0, 57.0) #(225.0, -25.0, 100.0, 22.0)
        pick_position = (200.0, 150.0, 20.38, 45) #(200.28, 119.57, 20.38, 38.43)
        sensor_position = (43.84, 240.0, 45.0, 86.45) #(43.84, 222.58, 43.59, 86.45) 

        # dobot to home position
        with log.timed("move_to_home_initial"):
            print("Drive to home...") # To Do: Delete print statement
            dobot1.move_to(*home_position)
            time.sleep(1)

        # start conveyor belt
        dobot1.ir_toggle(enable=True)

        with log.timed("conveyor_belt_running_until_object_detected"):
            print("Conveyor belt running") # To Do: Delete print statement
            dobot1.conveyor_belt.move(speed=0.5)
            # wait until object is detected
            while dobot1.get_ir() == False:
                time.sleep(0.1)

            print("Object detected - STOP") # To Do: Delete print statement
            dobot1.conveyor_belt.idle()
        log.info("object_detected_by_ir_sensor")

        # gripper opens
        with log.timed("gripper_open"):
            print("Gripper opens...") # To Do: Delete print statement
            dobot1.gripper.open()
            time.sleep(0.3)

        # arm drives to object
        with log.timed("move_to_pick"):
            print("Drive to object...") # To Do: Delete print statement
            dobot1.move_to(*pick_position)
            time.sleep(0.3)
 
        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot1.gripper.close()
            time.sleep(0.3)
            print("Gripper closed") # To Do: Delete print statement

        # put block on color sensor
        with log.timed("move_to_color_sensor"):
            print("Arm lifts up...") # To Do: Delete print statement
            dobot1.move_to(*sensor_position)
            time.sleep(0.3)

        # gripper opens
        with log.timed("gripper_open"):
            print("Gripper opens...") # To Do: Delete print statement
            dobot1.gripper.open()
            time.sleep(0.3)

        # arm back to home
        with log.timed("move_to_home_final"):
            print("Drive to home...") # To Do: Delete print statement
            dobot1.move_to(*home_position)
            time.sleep(1)

        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot1.gripper.close()
            time.sleep(1)
            print("Gripper closed") # To Do: Delete print statement

        # close connection
        dobot1.close()
        print("Fertig") # To Do: Delete print statement
        log.info("task_finished")

        print("Dobot 1 finished task") # To Do: Delete print statement

        client.publish("trackmodul_ah_SS26/dobot/pickplace/status", json.dumps({
            "status": "done"
        }), qos=1)

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("trackmodul_ah_SS26/dobot/pickplace/command")

client.loop_forever()