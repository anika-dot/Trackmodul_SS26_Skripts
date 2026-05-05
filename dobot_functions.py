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
resting = (219.4817, 5.5783, 85.0774, 1.4559)

def init_and_home_dobot(port, move_to_resting=False):
    try:
        print(f"Verwende Port: {port}")

        bot = Dobot(port)
        print(bot)

        print('Bot status:', 'connected' if bot.connected() else 'not connected')

        bot.interface.clear_alarms()
        bot.home()
        bot.interface.wait_until_done()

        sleep(3)

        return bot

    except Exception as e:
        print(f"Fehler bei Port {port}: {e}")
        return None

SAFE_Z = 120  # sichere Höhe über allen Objekten

def safe_move(bot, target, safe_z=SAFE_Z):
    x, y, z, r = target

    # 1. hochfahren (falls nicht schon oben)
    bot.move_to(x, y, safe_z, r, mode=1)
    sleep(3)

    # 2. XY Position sicher anfahren (oben)
    bot.move_to(x, y, safe_z, r, mode=1)
    sleep(3)

    # 3. runter zur Zielhöhe
    bot.move_to(x, y, z, r, mode=1)
    sleep(3)