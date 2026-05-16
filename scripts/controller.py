'''
This module acts as the controller for the whole process.
Both dobots and the color scanner act as subscriber to those topics and
the actions for them are handled in separate scripts.
'''

import time
import json
import paho.mqtt.client as mqtt
from event_logger import EventLogger

BROKER = "broker.hivemq.com"
state = "INIT"

log = EventLogger("controller")

def on_message(client, userdata, msg):
    '''
    Function to orchestrate the whole process with the involved components.
    '''
    global state

    data = json.loads(msg.payload.decode())
    topic = msg.topic

    print(f"[RECV] {topic} -> {data}")
    log.info("mqtt_received", topic=topic, payload=data)

    if topic == "trackmodul_ah_SS26/dobot/pickplace/status" and state == "WAIT_D_pickplace":
        log.end("pickplace_total")
        print("Start Color Sensor") # To Do: Delete print statement
        log.start("colorsensor_total")
        client.publish("trackmodul_ah_SS26/dobot/colorsensor/command", json.dumps({"command": "scanning"}))
        state = "WAIT_D_color_sensor"

    elif topic == "trackmodul_ah_SS26/dobot/colorsensor/status" and state == "WAIT_D_color_sensor":
        log.end("colorsensor_total")
        detected_color = data.get("color")

        print(f"Detected color: {detected_color}") # To Do: Delete print statement
        log.info("color_detected", color=detected_color)

        if detected_color == "blue":
            print("Start Dobot Sorter: BLUE") # To Do: Delete print statement
            log.start("sorter_total", color=detected_color)
            client.publish("trackmodul_ah_SS26/dobot/sorter/command", json.dumps({"command": "sorting blue"}))
        else:
            print("Start Dobot Sorter: OTHER") # To Do: Delete print statement
            log.start("sorter_total", color=detected_color)
            client.publish("trackmodul_ah_SS26/dobot/sorter/command", json.dumps({"command": "sorting other"}))
        
        state = "WAIT_D_Sorter"

    elif topic == "trackmodul_ah_SS26/dobot/sorter/status" and state == "WAIT_D_Sorter":
        log.end("sorter_total")
        print("Finished all tasks") # To Do: Delete print statement
        log.info("run_finished")
        #state = "DONE" # To Do: Delete
        ## Start the new process # To Do: Delete
        log.start("pickplace_total")
        client.publish("trackmodul_ah_SS26/dobot/pickplace/command", json.dumps({"command": "start"}))
        state = "WAIT_D_pickplace"
        

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe("trackmodul_ah_SS26/dobot/+/status")
# zusätzlicher Subscribe notwendig???? (pickplace???)

client.loop_start()

time.sleep(1)

print("Start Dobot Pick & Place") # To Do: Delete print statement
log.info("run_started")
log.start("pickplace_total")
client.publish("trackmodul_ah_SS26/dobot/pickplace/command", json.dumps({"command": "start"}))
state = "WAIT_D_pickplace"

# while state != "DONE": # To Do: Delete
#     time.sleep(1) # To Do: Delete

# Endlosschleife - läuft bis manuell gestoppt (Ctrl+C)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Process stopped by user")
    client.loop_stop()
    client.disconnect()