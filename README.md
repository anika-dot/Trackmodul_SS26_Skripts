# Trackmodul_SS26_Skripts

A Python-based automation system for coordinating two Dobot robotic arms in a sorting and handling workflow using MQTT messaging protocol. The setup contains a RaspberryPi, two Dobot Magician, a conveyor belt, a light barrier and a color sensor. 

## 💡 Overview

This project implements a distributed robotic control system featuring:
- **Central Controller** - Orchestrates the workflow between two Dobot robots, a conveyor belt, ligth barrier and color sensor
- **Pick & Place Unit** - Handles item manipulation using a Dobot robot
- **Color Sensor** - Identifies object colors for sorting decisions
- **Sorting Unit** - Sorts items based on detected colors (blue vs. other)
- **MQTT Communication** - Real-time message-based coordination between components

The system processes items through a complete workflow: pick-up → detection → sorting, with event logging and simple error handling.

## ✨ Features

- **Multi-Robot Orchestration** - Coordinate two Dobot arms via MQTT
- **Pick & Place Operations** - Automated manipulation with gripper control
- **Color-Based Sorting** - Automatic item classification by color detection
- **Event Logging** - Comprehensive logging of all system operations and timings
- **Safe Movement** - Protected movement commands with simple error handling
- **State Machine Control** - Robust workflow management with state tracking

## 👩‍💻 Tech Stack

- **Language**: Python 3
- **Primary Library**: 
  - `dobotapi` - Dobot robot control
  - `pydobotplus` - Extended Dobot functionality for color sensor
  - `paho-mqtt` - MQTT client for message brokering
  - `pyserial` - Serial communication
  - `pyyaml` - Configuration management
  - `coloredlogs` - Enhanced logging
- **Communication**: Public MQTT Broker (HiveMQ)
- **Platforms**: VisualStudioCode
- **Hardware**:
  - Dobot Magician with gripper arm, conveyor belt, light barrier and color sensor
  - RaspberryPi

### Set-up

- Dobot "Pickplace" with conveyor belt and light barrier
- Dobot "Sorter" with color sensor
- both Dobots connected to the same RaspberryPi

## 📦 Getting Started

### 🚀 Prerequisites

- Python 3.7+
- Hardware

### 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/anika-dot/Trackmodul_SS26_Skripts.git
   cd Trackmodul_SS26_Skripts
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **For color scanner module (optional)**
   ```bash
   cd color_scanner
   pip install -r requirements.txt
   ```

### 📖 Usage

#### Run all scripts together

Start the process 

```bash
./start_all.sh 
```

Stopp the process

```bash
./start_all.sh stop
```

Status of the process

```bash
./start_all.sh status
```

#### Run each script and 

**Initialize robot positions**:
```bash
source ~/venv/bin/activate
python homing_dobot.py
```

**Run the color sensor module**:
```bash
cd color_scanner
source ~/venv/bin/activate
python color_scanner.py
```

**Run the pick & place module**:
```bash
source ~/venv/bin/activate
python dobot_pickplace.py
```

**Run the sorting module**:
```bash
source ~/venv/bin/activate
python dobot_sorter.py
```

**Start the central controller** (main orchestration):
```bash
source ~/venv/bin/activate
python controller.py
```

If you need to refine the positions for the Dobots, use this interactive notebook to adjust them.

**Define custom positions** (interactive):
```bash
jupyter notebook define_positions.ipynb
```

### Get the Gantt Chart

To get the gantt chart of your process, run the following command in your terminal (you have to change the name of the log file):
```bash
python scripts/create_gantt.py logs/dobot_log_2026-05-19.jsonl --output gantt.png
```

### Get KPI and diagrams

To get the KPI and diagrams of your process, run the following command in your terminal (you have to change the name of the log file):
```bash
python scripts/generate_kpi.py logs/dobot_log_2026-05-19.jsonl 
```

## 🏗️ Project Structure

```
├── helper_functions/             # helper module
│   └── dobot_functions.py        # shared Dobot utility functions, import dobotmaster.lib.dobot
│   └── mqtt_handler.py           # MQTT communication utilities
│   └── event_logger.py           # event logger
│   └── dobotmaster/              # Dobot API integration layer
├── instructions/                 # instructions module
│   └── homing_dobot.ipynb        # interactive homing notebook
│   └── define_positions.ipynb    # position definition notebook
├── scripts/             		      # scripts module
│   └── controller.py             # central workflow orchestrator
│   └── dobot_sorter.py           # sorting logic with gripper control
│   └── dobot_pickplace.py        # pick & place operations
│   └── homing_dobot.py           # robot initialization script
│   └── create_gantt.py	        	# create gantt chart
│   └── generate_kpi.py           # generate kpi for a run
├── color_scanner/                # color detection module
│   └── scan_color.py			        # scan color
│   └── requirements.txt
├── logs/                         # log files
├── report/                       # report files
├── start_all.sh                  # file to start the whole process as one
├── pyproject.toml                # define project and define dependencies
├── requirements.txt              # python dependencies
└── README.md 
```

## 🔄 Workflow

The system operates as a state machine with the following workflow:

1. **INIT → WAIT_D_pickplace**: Controller starts pick & place operation
2. **WAIT_D_pickplace → WAIT_D_color_sensor**: Item picked up, now scan color
3. **WAIT_D_color_sensor → WAIT_D_Sorter**: Color detected, sort accordingly
4. **WAIT_D_Sorter → DONE**: Sorting complete, cycle finishes

Each operation is logged with timing information for performance analysis.

## 📡 MQTT Topics

- `trackmodul_ah_SS26/dobot/pickplace/command` - Pick & place commands
- `trackmodul_ah_SS26/dobot/pickplace/status` - Pick & place status
- `trackmodul_ah_SS26/dobot/colorsensor/command` - Color sensor commands
- `trackmodul_ah_SS26/dobot/colorsensor/status` - Color sensor status (includes detected color)
- `trackmodul_ah_SS26/dobot/sorter/command` - Sort commands (blue/other)
- `trackmodul_ah_SS26/dobot/sorter/status` - Sorter completion status

## 🐛 Issues

If you encounter any issues while using or setting up the project, please check the [Issues section](https://github.com/anika-dot/Trackmodul_SS26_Skripts/issues) to see if it has already been reported. If not, feel free to open a new issue detailing the problem.

### When reporting an issue, please include:

- A clear and descriptive title
- A detailed description of the problem
- Steps to reproduce the issue
- Any relevant logs or error messages (check `EventLogger` output)
- Screenshots of the error (if applicable)
- System information:
  - Operating System and version
  - Python version
  - Dobot model and firmware version
  - Serial port information
  - MQTT broker status

### Issues with the Dobot positions

You can find a guide to hanlde Dobot positions here: define_positions.ipynb 
If you encounter problems with the homing position of the Dobot, you can take a look at this notebook: homing_dobot.ipynb. In the guide you will find detailed information how to reset the dobot home position and change it. 

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

**Project**: Trackmodul SS26 (Summer Semester 2026)  
**Author**: [@anika-dot](https://github.com/anika-dot)  
**Status**: Active Development
