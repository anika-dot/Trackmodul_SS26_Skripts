from serial.tools import list_ports
from serial import Serial, SerialException

# Find all available Dobot ports
def find_dobot_ports():
    ports = []
    for p in list_ports.comports():
        desc = (p.description or "").upper()
        if any(k in desc for k in ("CP210", "USB", "UART", "SLAB")):
            ports.append(p.device)
    return ports

def ensure_port_openable(port):
    try:
        s = Serial(port=port, baudrate=115200, timeout=0.1)
        s.close()
        return True
    except SerialException:
        return False

ports = find_dobot_ports()
if not ports:
    raise RuntimeError("Keine Dobots gefunden. Treiber/Kabel prüfen.")

# Check, which ports are actually openable
open_ports = [p for p in ports if ensure_port_openable(p)]
print(f"Gefundene Dobot-Ports: {open_ports}")
print(f"Port1: {open_ports[0]}")
print(f"Port2: {open_ports[1]}")
print(ports[0])



from time import sleep
from dobotmaster.lib.dobot import Dobot
from serial.tools import list_ports

# Resting (home) position of the Dobot
resting = (219.4817, 20, 85.0774, 1.4559) #(219.4817, 5.20, 85.0774, 1.4559)

def init_and_home_dobot(port, move_to_resting=False):
    try:
        print(f"Verwende Port: {port}")

        bot = Dobot(port)
        print(bot)

        print('Bot status:', 'connected' if bot.connected() else 'not connected')

        bot.interface.clear_alarms()
        bot.home()
        bot.interface.wait_until_done()

        sleep(1)

        return bot

    except Exception as e:
        print(f"Fehler bei Port {port}: {e}")
        return None

SAFE_Z = 120  # sichere Höhe über allen Objekten

# def safe_move(bot, target, safe_z=SAFE_Z):
#     x, y, z, r = target

#     # 1. hochfahren (falls nicht schon oben)
#     bot.move_to(x, y, safe_z, r, mode=1)
#     sleep(1)

#     # 2. XY Position sicher anfahren (oben)
#     #bot.move_to(x, y, safe_z, r, mode=1)
#     #sleep(1)

#     # 3. runter zur Zielhöhe
#     bot.move_to(x, y, z, r, mode=1)
#     sleep(1)

def safe_move(bot, target, safe_z=SAFE_Z):
    x, y, z, r = target

    # 1. aktuelle Position holen
    # cur_x, cur_y, cur_z, cur_r = bot.get_pose()
    # print("Aktuelle Position:", bot.get_pose())
    pose = bot.get_pose()

    cur_x = pose.position.x
    cur_y = pose.position.y
    cur_z = pose.position.z
    cur_r = pose.position.rotation

    # 2. erst senkrecht hoch
    if cur_z < safe_z:
        bot.move_to(cur_x, cur_y, safe_z, cur_r, mode=1)
        sleep(1)

    # 3. XY über safe_z fahren
    bot.move_to(x, y, safe_z, r, mode=1)
    sleep(1)

    # 4. runter zur Zielhöhe
    bot.move_to(x, y, z, r, mode=1)
    sleep(1)