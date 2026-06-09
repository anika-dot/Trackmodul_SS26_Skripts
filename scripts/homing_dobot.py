'''
This module is used to initialize and home the Dobots, and print their status. 
Make sure to adjust the port selection in the code if necessary, 
as the order of the ports may vary on different systems.
'''

import time
from helper_functions.dobot_functions import find_dobot_ports, init_and_home_dobot

ports = find_dobot_ports()
print(ports)

# Choose the correct ports for the two Dobots (you may need to adjust this based on your system)
dobot_pickplace = init_and_home_dobot(ports[0])
dobot_sorter = init_and_home_dobot(ports[1])

time.sleep(1)

print("Dobot pickplace:", dobot_pickplace)
print("Dobot sorter:", dobot_sorter)

# Close connections at the end of the script
dobot_pickplace.interface.close_col()
dobot_sorter.interface.close_col()
