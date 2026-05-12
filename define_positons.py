
from dobot_functions import find_dobot_ports, init_and_home_dobot, safe_move
import time

ports = find_dobot_ports()
print(ports)

# Richtige Ports wählen!
dobot = init_and_home_dobot(ports[1])

time.sleep(1)

print("dobot:", dobot)

# Positionen
# Home: 209.6999969482422, 0.0, 100.0, 0.0
pick_color_sensor_sorter = (150, -190, 50, 65)
throw_position_sorter = (250, 100, 50, 0) 
conveyor_position_sorter = (230, -50, 50, 0)
pick_conveyor_belt_pick_place = (230, 85, 30, 55)
place_color_sensor_pick_place = (150, 255, 50, 45)

safe_move(dobot, place_color_sensor_pick_place)

time.sleep(0.5)

# ERST AM ENDE schließen
dobot.interface.close_col()