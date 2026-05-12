from dobotmaster.lib.dobot import Dobot
from dobot_functions import find_dobot_ports
from time import sleep
 
ports = find_dobot_ports()
 
for port in ports:
    print(f"\n--- {port} ---")
    bot = Dobot(port)
    # Aktuelle Werte anschauen
    print("Homing-Params vorher:", bot.interface.get_homing_paramaters())
    print("End-Effector-Params:", bot.interface.get_end_effector_params())
    bot.interface.close_col()