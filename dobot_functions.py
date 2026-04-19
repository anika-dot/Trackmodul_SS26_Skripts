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