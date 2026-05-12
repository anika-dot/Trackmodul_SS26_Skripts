# from dobotapi import Dobot
# import time

# from dobot_functions import find_dobot_ports
# from dobot_functions import init_and_home_dobot

# # Connect to dobot 1
# ports = find_dobot_ports()
# dobot1 = Dobot(port=ports[1])
# dobot1.connect()
# print(ports)

# dobot2 = Dobot(port=ports[2])
# dobot2.connect()

# # Warte kurz damit Verbindung stabil ist
# time.sleep(0.2)

# dobot1 = init_and_home_dobot()

# if dobot1:
#     print("Dobot 1 ist bereit!")
#     dobot1.interface.close_col()
# time.sleep(5)

# dobot2 = init_and_home_dobot()
# if dobot2:
#     print("Dobot 2 ist bereit!")
#     dobot2.interface.close_col()
# time.sleep(5)

# pos1 = dobot1.get_pose()  
# pos2 = dobot2.get_pose()

# #Print positions of both dobots
# print("Dobot 1 Position:")
# print(pos1)

# print("Dobot 2 Position:")
# print(pos2)


# # Position needed for start:
# # Dobot 1 Position:
# # Pose(position=Position(x=240.96795654296875, y=104.80534362792969, z=24.216232299804688, rotation=23.50589942932129), joints=Joints(jointA=23.50589942932129, jointB=37.319984436035156, jointC=34.444419860839844, jointD=0.0))
# # Dobot 2 Position:
# # Pose(position=Position(x=229.54664611816406, y=69.9216537475586, z=11.747283935546875, rotation=16.94113540649414), joints=Joints(jointA=16.94113540649414, jointB=33.11714172363281, jointC=43.57234191894531, jointD=0.0))

# # 

from dobot_functions import find_dobot_ports, init_and_home_dobot, safe_move
import time

ports = find_dobot_ports()
print(ports)

# ✅ Richtige Ports wählen!
dobot1 = init_and_home_dobot(ports[0])
dobot2 = init_and_home_dobot(ports[1])

time.sleep(1)

print("dobot1:", dobot1)
print("dobot2:", dobot2)

dobot1

# ❗ NICHT vorher schließen!
pos1 = dobot1.get_pose()
pos2 = dobot2.get_pose()

# Positionen
pick_color_sensor_sorter = (150, -150, 50, 5)
pick_conveyor_belt_pick_place = (100, 150, 60, 0)

safe_move(dobot1, pick_color_sensor_sorter)
safe_move(dobot2, pick_conveyor_belt_pick_place)

time.sleep(0.5)

print("Dobot 1 Position:", pos1)
# Dobot 1 Position: (209.61517333984375, 6.482858589151874e-05, 100.03802490234375, 1.772011091816239e-05, 1.772011091816239e-05, 3.00955867767334, 13.684184074401855, 0.0)
print("Dobot 2 Position:", pos2)
# Dobot 2 Position: (259.1121520996094, -0.00018619498587213457, -8.416336059570312, -4.1172083001583815e-05, -4.1172083001583815e-05, 44.981719970703125, 44.97877883911133, 0.0)

# ✅ ERST AM ENDE schließen
dobot1.interface.close_col()
dobot2.interface.close_col()

# Home positonen:
# Dobot Sorter Position: (209.77276611328125, 6.487732753157616e-05, 99.93025970458984, 1.772011091816239e-05, 1.772011091816239e-05, 3.08670711517334, 13.72353744506836, 0.0)
# Dobot Pick and Place Position: (259.064697265625, -0.0001861608907347545, -8.409278869628906, -4.1172083001583815e-05, -4.1172083001583815e-05, 44.96536636352539, 44.98990249633789, 0.0)