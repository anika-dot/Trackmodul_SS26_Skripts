
from dobot_functions import find_dobot_ports, init_and_home_dobot, safe_move
import time

ports = find_dobot_ports()
print(ports)

# ✅ Richtige Ports wählen!
dobot = init_and_home_dobot(ports[0])

time.sleep(1)

print("dobot:", dobot)

# ✅ ERST AM ENDE schließen
dobot.interface.close_col()