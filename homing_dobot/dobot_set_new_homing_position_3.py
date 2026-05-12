from dobotmaster.lib.dobot import Dobot
from dobot_functions import find_dobot_ports
from time import sleep
 
# Nur den "kaputten" Dobot ACM1 fixen
bot = Dobot('/dev/ttyACM1')
 
# Werte von ACM0 übernehmen
bot.interface.set_homing_parameters(209.70, 0.0, 100.0, 0.0)
print("Homing-Parameter gesetzt. Starte Homing...")
 
# Neu homen, damit die Werte aktiv werden
bot.home()
bot.interface.wait_until_done()
sleep(2)
 
# Verifizieren
print("Neue Pose nach Homing:", bot.get_pose())
print("Neue Homing-Params:", bot.interface.get_homing_paramaters())
 
bot.interface.close_col()