from serial.tools import list_ports
from serial import Serial, SerialException
from time import sleep
from dobotmaster.lib.dobot import Dobot

SAFE_Z = 100  # save height for moving in XY plane without hitting anything


# Find all available Dobot ports
def find_dobot_ports():
    '''
    Find all available Dobot ports by looking for typical USB-to-serial converter keywords in the port description.
    '''
    ports = []
    for p in list_ports.comports():
        desc = (p.description or "").upper()
        if any(k in desc for k in ("CP210", "USB", "UART", "SLAB")):
            ports.append(p.device)
    return ports

def ensure_port_openable(port):
    '''
    Check if the given port can be opened. This is a sanity check to filter out ports that are not actually usable for connecting to a Dobot.
    '''
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
# open_ports = [p for p in ports if ensure_port_openable(p)]
# print(f"Gefundene Dobot-Ports: {open_ports}")
# print(f"Port1: {open_ports[0]}")
# print(f"Port2: {open_ports[1]}")
# print(ports[0])

def init_and_home_dobot(port, move_to_resting=False):
    '''
    Initialize the Dobot on the given port, home it, and optionally move it to a resting position.
    '''
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

def safe_move(bot, target, safe_z=SAFE_Z):
    '''
    Move the Dobot to the target position (x, y, z, r) in a safe manner by first moving up to a safe Z height, then moving in XY plane, and finally moving down to the target Z.
    '''
    x, y, z, r = target

    # 1. get current pose
    pose = bot.get_pose()

    cur_x = pose.position.x
    cur_y = pose.position.y
    cur_z = pose.position.z
    cur_r = pose.position.rotation

    # 2. move up vertically from current position if below safe_z
    if cur_z < safe_z:
        bot.move_to(cur_x, cur_y, safe_z, cur_r, mode=1)
        sleep(1)

    # 3. drive to target XY position
    bot.move_to(x, y, safe_z, r, mode=1)
    sleep(1)

    # 4. move down vertically to target Z
    bot.move_to(x, y, z, r, mode=1)
    sleep(1)