
from dobot_functions import find_dobot_ports, init_and_home_dobot, safe_move
import time

ports = find_dobot_ports()
print(ports)

# ✅ Richtige Ports wählen!
dobot_pickplace = init_and_home_dobot(ports[0])
dobot_sorter = init_and_home_dobot(ports[1])

time.sleep(1)

print("dobot pickplace:", dobot_pickplace)
print("dobot sorter:", dobot_sorter)

# ✅ ERST AM ENDE schließen
dobot_pickplace.interface.close_col()
dobot_sorter.interface.close_col()