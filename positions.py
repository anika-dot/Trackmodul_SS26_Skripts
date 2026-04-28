from dobotapi import Dobot
import time

from dobot_functions import find_dobot_ports

# Connect to dobot 1
ports = find_dobot_ports()
dobot1 = Dobot(port=ports[0])
dobot1.connect()
print(ports)

dobot2 = Dobot(port=ports[1])
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


# Position needed for start:
# Dobot 1 Position:
# Pose(position=Position(x=240.96795654296875, y=104.80534362792969, z=24.216232299804688, rotation=23.50589942932129), joints=Joints(jointA=23.50589942932129, jointB=37.319984436035156, jointC=34.444419860839844, jointD=0.0))
# Dobot 2 Position:
# Pose(position=Position(x=229.54664611816406, y=69.9216537475586, z=11.747283935546875, rotation=16.94113540649414), joints=Joints(jointA=16.94113540649414, jointB=33.11714172363281, jointC=43.57234191894531, jointD=0.0))