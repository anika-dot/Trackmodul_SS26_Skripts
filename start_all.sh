#!/bin/bash
# ============================================================
# Centralized startup script for all processes in the trackmodule SS26 project.
# Starts all 4 processes in separate terminals / tmux panes.
# To stop: ./start_all.sh stop
# ============================================================

BASE_DIR="$HOME/Trackmodul_SS26_Skripts"
COLOR_DIR="$BASE_DIR/color_scanner"
PID_FILE="/tmp/trackmodul_pids.txt"

start_all() {
    echo "Start all trackmodule processes..."

    # 0) Home both Dobots first
    echo ""
    echo "Homing both Dobots..."
    (
        cd "$BASE_DIR" || exit 1
        source venv/bin/activate
        python scripts/homing_dobot.py
    )
    HOMING_EXIT=$?

    if [ $HOMING_EXIT -ne 0 ]; then
        echo ""
        echo "Homing failed, stopping all processes."
        echo "    Please check both Dobots and ensure they are properly connected and can move freely."
        exit 1
    fi

    echo "Homing successful, starting main processes..."
    echo ""
    sleep 1   # short pause before starting main processes

    # Delete old PID file if exists
    rm -f "$PID_FILE"

    # 1) color_scanner – separate venv
    (
        cd "$COLOR_DIR" || exit 1
        source venv/bin/activate
        python scan_color.py &
        echo $! >> "$PID_FILE"
        wait
    ) &
    echo "Color scanner started (PID $!)"

    sleep 0.5   # short pause, so ports don't collide

    # 2) dobot_sorter – main -venv
    (
        cd "$BASE_DIR" || exit 1
        source venv/bin/activate
        python scripts/dobot_sorter.py &
        echo $! >> "$PID_FILE"
        wait
    ) &
    echo "Dobot sorter started (PID $!)"

    sleep 0.5

    # 3) dobot_pickplace – main -venv
    (
        cd "$BASE_DIR" || exit 1
        source venv/bin/activate
        python scripts/dobot_pickplace.py &
        echo $! >> "$PID_FILE"
        wait
    ) &
    echo "Dobot pickplace started (PID $!)"

    sleep 0.5

    # 4) controller – main -venv (last, as it depends on the others)
    (
        cd "$BASE_DIR" || exit 1
        source venv/bin/activate
        python scripts/controller.py &
        echo $! >> "$PID_FILE"
        wait
    ) &
    echo "Controller started (PID $!)"

    echo ""
    echo "All processes started. Stop with:  ./start_all.sh stop"
    echo "    (or with the GUI: python launcher_gui.py)"
}

stop_all() {
    echo "Stopping all processes..."

    # Stop processes by name, then by PID if needed
    for script in scan_color.py dobot_sorter.py dobot_pickplace.py controller.py; do
        if pkill -f "$script" 2>/dev/null; then
            echo "  ✓ $script stopped"
        else
            echo "  – $script not running"
        fi
    done

    # Wait a moment to ensure processes have stopped
    sleep 1
    for script in scan_color.py dobot_sorter.py dobot_pickplace.py controller.py; do
        pkill -9 -f "$script" 2>/dev/null
    done

    rm -f "$PID_FILE"
    echo "All processes stopped."
}

status_all() {
    echo "Status:"
    for script in scan_color.py dobot_sorter.py dobot_pickplace.py controller.py homing_dobot.py; do
        if pgrep -f "$script" > /dev/null; then
            echo "  🟢  $script running (PID: $(pgrep -f "$script"))"
        else
            echo "  🔴  $script stopped"
        fi
    done
}

case "${1:-start}" in
    start)  start_all ;;
    stop)   stop_all  ;;
    status) status_all ;;
    restart)
        stop_all
        sleep 1
        start_all
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac