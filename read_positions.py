from dobotapi import Dobot
from dobot_functions import find_dobot_ports
import time

ports = find_dobot_ports()
print(f"Verfügbare Ports: {ports}")

# Wähle den richtigen Dobot - 0 oder 1 anpassen
dobot = Dobot(port=ports[0])
dobot.connect()
print("Dobot verbunden")

# Motoren ausschalten -> Arm wird "schlaff" und lässt sich von Hand bewegen
# dobot.set_motor(enable=False)  # API-Name evtl. anders, siehe unten
# dobot.disable()  # oder dobot.disable() - je nach API
# dobot.device.clear_alarms() #funktioniert auch nicht

print("\nBewege den Arm jetzt von Hand zur gewünschten Position.")
print("Drücke ENTER um die Position zu printen, Ctrl+C zum Beenden.\n")

try:
    while True:
        input("ENTER drücken zum Auslesen...")
        pose = dobot.get_pose()  # API-Name evtl. anders
        x, y, z, r = pose[0], pose[1], pose[2], pose[3]
        print(f"  Position: ({x:.2f}, {y:.2f}, {z:.2f}, {r:.2f})")
except KeyboardInterrupt:
    print("\nBeendet.")
finally:
    dobot.close()


###################################
#### Oder speichern #################
#####################################


# from dobotapi import Dobot
# from dobot_functions import find_dobot_ports
# import time

# ports = find_dobot_ports()
# dobot = Dobot(port=ports[0])  # oder ports[1] - den richtigen wählen!
# dobot.connect()

# # Motoren deaktivieren -> Arm wird "schlaff" und kann von Hand bewegt werden
# dobot.set_motor(enable=False)  # je nach API: dobot.disable() oder ähnlich

# print("Bewege den Arm von Hand zur gewünschten Position.")
# print("Drücke ENTER um die Position zu speichern, 'q' zum Beenden.")

# positions = {}
# while True:
#     name = input("Name der Position (oder 'q'): ")
#     if name == "q":
#         break
#     pose = dobot.get_pose()  # gibt (x, y, z, r) zurück
#     positions[name] = pose
#     print(f"  Gespeichert: {name} = {pose}")

# print("\n--- Alle Positionen ---")
# for name, pose in positions.items():
#     print(f"{name} = {pose}")
