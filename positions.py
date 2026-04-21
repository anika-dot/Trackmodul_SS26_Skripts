from dobotapi import Dobot
import time

from dobot_functions import find_dobot_ports

# Connect to dobot 1
ports = find_dobot_ports()
dobot1 = Dobot(port=ports[1])
dobot1.connect()
print(ports)

dobot2 = Dobot(port=ports[0])
dobot2.connect()

# Warte kurz damit Verbindung stabil ist
time.sleep(0.2)

pos1 = dobot1.get_pose()  
pos2 = dobot2.get_pose()

#Print positions of both dobots
print("Dobot 1 Position:")
print(pos1)

print("Dobot 2 Position:")
print(pos2)
