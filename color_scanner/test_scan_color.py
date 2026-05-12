import json
import time
from turtle import color
from xml.etree.ElementTree import VERSION
from xmlrpc import client
from dobot_functions import find_dobot_ports
from pydobotplus import Dobot


# Connect to color sensor
ports = find_dobot_ports()
color_sensor = Dobot(port=ports[0])

print("Color sensor ready")


print("Color sensor start scanning")

VERSION = 2  # Set to 2 for Dobot Magician, 1 for Dobot M1

color_sensor.set_color(True, VERSION)

# Reading color sensor...
print("Reading color sensor...")
color_sensor.get_color()
rgb = color_sensor.get_color()
time.sleep(0.3)
print("Color sensor finished scanning")

if rgb == [False, False, True]:
    color = "blue"
else:
    color = "other"

print(f"Detected color: {color}")