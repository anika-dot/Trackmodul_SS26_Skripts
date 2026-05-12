from dobotmaster.lib.dobot import Dobot
from dobot_functions import find_dobot_ports
from time import sleep
 
ports = find_dobot_ports()
 
for i, port in enumerate(ports):
    print(f"\n=== Dobot {i} an Port {port} ===")
    bot = Dobot(port)
    bot.interface.clear_alarms()
    bot.home()
    bot.interface.wait_until_done()
    sleep(2)
    pose = bot.get_pose()
    print(f"Pose nach Homing: {pose}")
    print(f"Verfügbare interface-Methoden:")
    print([m for m in dir(bot.interface) if 'home' in m.lower() or 'param' in m.lower()])
    bot.interface.close_col()