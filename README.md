# Trackmodul_SS26_Skripts

A Python-based automation system for coordinating two Dobot robotic arms in a sorting and handling workflow using MQTT messaging protocol. The setup contains a RaspberryPi, two Dobot Magician robots, a conveyor belt, a light barrier, and a color sensor.

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

### Known limitation:
- The color sensor currently distinguishes only between blue and non-blue objects. 
- The public HiveMQ MQTT broker provides no authentication — all messages are visible to anyone using the same topic prefix.

## 👩‍💻 Tech Stack

- **Language**: Python 3
- **Communication**: Public MQTT Broker (HiveMQ)
- **Platforms**: VisualStudioCode

### Main Libraries

| Library | Purpose |
|----------|----------|
| `dobotapi` | Dobot robot control |
| `pydobotplus` | Extended Dobot functionality for color sensor |
| `paho-mqtt` | MQTT communication |
| `pyserial` | Serial communication |
| `pyyaml` | Configuration management |
| `coloredlogs` | Enhanced logging |
| `streamlit` | Dashboard visualization |
| `pandas` | KPI calculation and data analysis |
| `matplotlib` | KPI and process visualization |

### Python Environments

The project uses **two separate virtual environments**:

#### Main Control Environment

Used for:
- Controller
- Pick & Place Dobot
- Sorting Dobot
- Dashboard
- KPI generation

Dependencies are defined in:

```text
requirements.txt
```

#### Color Scanner Environment

Used for:
- Color sensor module (`color_scanner/scan_color.py`)

Dependencies are defined in:

```text
color_scanner/requirements.txt
```

### Hardware

- Dobot Magician "Pickplace" — with gripper arm, conveyor belt, and light barrier
- Dobot Magician "Sorter" — with gripper arm and color sensor
- Raspberry Pi (both Dobots connected via USB)

## 📦 Getting Started

### 🚀 Prerequisites

- Python 3.7+
- RaspberryPi (tested on RaspberryPi OS)
- Both Dobot Magician robots connected to the same Raspberry Pi
- Jupyter Notebook (for position definition notebooks): `pip install notebook`

### 🔌 Hardware Setup
Connect both Dobots to the Raspberry Pi via USB. Check which serial port each Dobot is assigned to:

```bash
ls /dev/ttyUSB*
```

Typical assignment (may vary):
| Dobot | Port |
|-------|------|
| Pickplace | `/dev/ttyUSB0` |
| Sorter | `/dev/ttyUSB1` |

Update the serial port configuration in the respective scripts (`dobot_pickplace.py`, `dobot_sorter.py`) if your assignment differs.

### ⚙️ Configuration
The project uses a YAML-based configuration. Before running, verify the following in your config file:
- Serial ports for each Dobot
- MQTT broker address and topic prefix (`trackmodul_ah_SS26/...`)
- Pick, place, and sort positions (see `define_positions.ipynb`)

### 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/anika-dot/Trackmodul_SS26_Skripts.git
   cd Trackmodul_SS26_Skripts
   ```

2. **Create the main virtual environment**
   ```bash
   python3 -m venv ~/venv_main
   source ~/venv_main/bin/activate
   pip install -r requirements.txt
   ```

3. **Create the color scanner virtual environment**
   ```bash
   python3 -m venv ~/venv_color
   source ~/venv_color/bin/activate

   cd color_scanner
   pip install -r requirements.txt
   cd ..
   ```

### 📖 Usage

#### Run everything at once (recommended)

```bash
# Start all components
./start_all.sh

# Stop all components
./start_all.sh stop

# Check status
./start_all.sh status
```

#### Run each component individually

Always activate the virtual environment first:

For controller, pick & place, sorter, dashboard and KPI generation:

```bash
source ~/venv_main/bin/activate
```

For the color scanner:

```bash
source ~/venv_color/bin/activate
```

**1. Initialize robot positions** (run once before first use):
```bash
python scripts/homing_dobot.py
```

**2. Start the color sensor module**:
```bash
cd color_scanner
python scan_color.py
cd ..
```

**3. Start the pick & place module**:
```bash
python scripts/dobot_pickplace.py
```

**4. Start the sorting module**:
```bash
python scripts/dobot_sorter.py
```

**5. Start the central controller** (main orchestration — start this last):
```bash
python scripts/controller.py
```

#### Define custom positions

Use the interactive notebook to adjust robot positions:

```bash
jupyter notebook instructions/define_positions.ipynb
```

#### Generate analysis outputs

To get the KPI and diagrams of your process, run the following command in your terminal (you have to change the name of the log file):
```bash
python scripts/generate_kpi.py logs/dobot_log_2026-05-19.jsonl 
```

#### Start dashboard

To start the dashboard and see all plots and outputs in one file, use this code:
```bash
streamlit run dashboard.py
```

## 🏗️ Project Structure

```
├── helper_functions/            # Shared utilities
│   ├── dobot_functions.py       # Shared Dobot utility functions
│   ├── mqtt_handler.py          # MQTT communication utilities
│   ├── event_logger.py          # Event logger (outputs to logs/)
│   └── dobotmaster/             # Dobot API integration layer
├── instructions/                # Developer tools (interactive notebooks)
│   ├── homing_dobot.ipynb       # Interactive homing guide
│   └── define_positions.ipynb   # Position definition and tuning
│   └── set_up_raspberrypi.ipynb # Set-up RaspberryPi
│   └── test_color_scan.ipynb    # Test the color scanner
├── scripts/                     # Main runnable scripts
│   ├── controller.py            # Central workflow orchestrator
│   ├── dobot_sorter.py          # Sorting logic with gripper control
│   ├── dobot_pickplace.py       # Pick & place operations
│   ├── homing_dobot.py          # Robot initialization (run once)
│   ├── dashboard.py             # Generate Dashboard from log
│   └── generate_kpi.py          # Generate KPIs and diagrams from log
├── color_scanner/               # Color detection module
│   ├── scan_color.py            # Color scan logic
│   └── requirements.txt         # Color scanner dependencies
├── logs/                        # Auto-generated JSONL log files
├── report/                      # Auto-generated KPI outputs (charts, summaries)
├── start_all.sh                 # Start/stop/status for all components
├── pyproject.toml               # Project metadata and dependencies
├── requirements.txt             # Python dependencies
└── README.md
```

**Note:** The `instructions/` folder contains developer notebooks for setup and calibration, not part of the regular runtime workflow.

## 🔄 Workflow

TThe system operates as a state machine:

```
INIT → WAIT_D_pickplace → WAIT_D_color_sensor → WAIT_D_Sorter → DONE
```

1. **INIT → WAIT_D_pickplace** — Controller triggers pick & place operation
2. **WAIT_D_pickplace → WAIT_D_color_sensor** — Item picked up; color scan starts
3. **WAIT_D_color_sensor → WAIT_D_Sorter** — Color detected; sort command sent
4. **WAIT_D_Sorter → DONE** — Sorting complete; cycle finishes and restarts

Each operation is logged with timestamps to `logs/` for later analysis.

## 📡 MQTT Topics


| Topic | Direction | Description |
|-------|-----------|-------------|
| `trackmodul_ah_SS26/dobot/pickplace/command` | Controller → Pickplace | Start pick & place |
| `trackmodul_ah_SS26/dobot/pickplace/status` | Pickplace → Controller | Done / error |
| `trackmodul_ah_SS26/dobot/colorsensor/command` | Controller → Sensor | Start color scan |
| `trackmodul_ah_SS26/dobot/colorsensor/status` | Sensor → Controller | Detected color |
| `trackmodul_ah_SS26/dobot/sorter/command` | Controller → Sorter | Sort `blue` or `other` |
| `trackmodul_ah_SS26/dobot/sorter/status` | Sorter → Controller | Sort complete |

## 🐛 Issues

Check the `logs/` directory and `EventLogger` output first — most issues are logged with timestamps.

**Dobot not connecting?** Verify the serial port with `ls /dev/ttyUSB*` and update the config accordingly.

**Wrong positions?** Use the interactive notebooks:
- Position calibration: `instructions/define_positions.ipynb`
- Homing issues: `instructions/homing_dobot.ipynb`

For other issues, open a ticket in the [Issues section](https://github.com/anika-dot/Trackmodul_SS26_Skripts/issues) and include: Python version, Dobot firmware version, serial port info, MQTT broker status, and the relevant log output.

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

**Project**: Trackmodul SS26 (Summer Semester 2026)  
**Author**: [@anika-dot](https://github.com/anika-dot)  
**Status**: Active Development
