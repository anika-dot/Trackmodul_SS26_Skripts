import json
import time
import paho.mqtt.client as mqtt
from dobotapi import Dobot
from dobot_functions import find_dobot_ports, safe_move
from event_logger import EventLogger

BROKER = "broker.hivemq.com"

log = EventLogger("pickplace")

# Connect to dobot 1
ports = find_dobot_ports()
dobot1 = Dobot(port=ports[0])
dobot1.connect()
log.info("dobot_connected", port=ports[1])
print("Dobot Pick & Place ready") # To Do: Delete print statement

HOME_POSITION = (209.6999969482422, 0.0, 100.0, 0.0) # given from the dobot
PICK_POSITION = (230, 85, 30, 55) #checked
SENSOR_POSITION = (150, 255, 50, 45) #checked

SLEEP_TIME = 1

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    if data.get("command") == "start":
        print("Dobot Pick & Place start task") # To Do: Delete print statement
        log.info("task_received", command="start")

        # dobot to home position
        with log.timed("move_to_home_initial"):
            print("Drive to home...") # To Do: Delete print statement
            safe_move(dobot1, HOME_POSITION)
            time.sleep(SLEEP_TIME)

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
            time.sleep(SLEEP_TIME)

        # arm drives to object
        with log.timed("move_to_pick"):
            print("Drive to object...") # To Do: Delete print statement
            safe_move(dobot1, PICK_POSITION)
            time.sleep(SLEEP_TIME)
 
        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot1.gripper.close()
            time.sleep(SLEEP_TIME)
            print("Gripper closed") # To Do: Delete print statement

        # put block on color sensor
        with log.timed("move_to_color_sensor"):
            print("Arm lifts up...") # To Do: Delete print statement
            safe_move(dobot1, SENSOR_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper opens
        with log.timed("gripper_open"):
            print("Gripper opens...") # To Do: Delete print statement
            dobot1.gripper.open()
            time.sleep(SLEEP_TIME)

        # arm back to home
        with log.timed("move_to_home_final"):
            print("Drive to home...") # To Do: Delete print statement
            safe_move(dobot1, HOME_POSITION)
            time.sleep(SLEEP_TIME)

        # gripper closes
        with log.timed("gripper_close"):
            print("Gripper closes...") # To Do: Delete print statement
            dobot1.gripper.close()
            time.sleep(SLEEP_TIME)
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