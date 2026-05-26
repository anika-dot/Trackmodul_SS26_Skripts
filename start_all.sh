#!/bin/bash
# ============================================================
#  Trackmodul SS26 – Zentrales Startskript
#  Startet alle 4 Prozesse in separaten Terminals / tmux-Panes
#  Beenden: ./start_all.sh stop
# ============================================================

BASE_DIR="$HOME/Trackmodul_SS26_Skripts"
COLOR_DIR="$BASE_DIR/color_scanner"
PID_FILE="/tmp/trackmodul_pids.txt"

start_all() {
    echo "▶  Starte Trackmodul SS26 Prozesse..."

    # ── 0) Homing beider Dobots ──────────────────────────────────────────────
    echo ""
    echo "🏠  Homing Dobots (bitte warten bis abgeschlossen)..."
    (
        cd "$BASE_DIR" || exit 1
        source venv/bin/activate
        python scripts/homing_dobot.py
    )
    HOMING_EXIT=$?

    if [ $HOMING_EXIT -ne 0 ]; then
        echo ""
        echo "❌  Homing fehlgeschlagen (Exit-Code $HOMING_EXIT). Prozesse werden NICHT gestartet."
        echo "    Bitte Verbindung zu den Dobots prüfen und erneut versuchen."
        exit 1
    fi

    echo "  ✓ Homing abgeschlossen"
    echo ""
    sleep 1   # kurze Pause nach dem Homing

    # Alte PID-Datei löschen
    rm -f "$PID_FILE"

    # 1) color_scanner – eigenes venv
    (
        cd "$COLOR_DIR" || exit 1
        source venv/bin/activate
        python scan_color.py &
        echo $! >> "$PID_FILE"
        wait
    ) &
    echo "  ✓ scan_color.py gestartet (PID $!)"

    sleep 0.5   # kurze Pause, damit Ports nicht kollidieren

    # 2) dobot_sorter – Haupt-venv
    (
        cd "$BASE_DIR" || exit 1
        source venv/bin/activate
        python scripts/dobot_sorter.py &
        echo $! >> "$PID_FILE"
        wait
    ) &
    echo "  ✓ dobot_sorter.py gestartet (PID $!)"

    sleep 0.5

    # 3) dobot_pickplace – Haupt-venv
    (
        cd "$BASE_DIR" || exit 1
        source venv/bin/activate
        python scripts/dobot_pickplace.py &
        echo $! >> "$PID_FILE"
        wait
    ) &
    echo "  ✓ dobot_pickplace.py gestartet (PID $!)"

    sleep 0.5

    # 4) controller – Haupt-venv (zuletzt, da oft der Orchestrator)
    (
        cd "$BASE_DIR" || exit 1
        source venv/bin/activate
        python scripts/controller.py &
        echo $! >> "$PID_FILE"
        wait
    ) &
    echo "  ✓ controller.py gestartet (PID $!)"

    echo ""
    echo "✅  Alle Prozesse laufen. Stoppen mit:  ./start_all.sh stop"
    echo "    (oder mit der GUI: python launcher_gui.py)"
}

stop_all() {
    echo "⏹  Stoppe alle Trackmodul-Prozesse..."

    # Direkt nach Skriptnamen killen – zuverlässigste Methode
    for script in scan_color.py dobot_sorter.py dobot_pickplace.py controller.py; do
        if pkill -f "$script" 2>/dev/null; then
            echo "  ✓ $script gestoppt"
        else
            echo "  – $script lief nicht"
        fi
    done

    # Kurz warten, dann mit SIGKILL nachschlagen falls nötig
    sleep 1
    for script in scan_color.py dobot_sorter.py dobot_pickplace.py controller.py; do
        pkill -9 -f "$script" 2>/dev/null
    done

    rm -f "$PID_FILE"
    echo "✅  Alle Prozesse gestoppt."
}

status_all() {
    echo "📋  Status Trackmodul-Prozesse:"
    for script in scan_color.py dobot_sorter.py dobot_pickplace.py controller.py homing_dobot.py; do
        if pgrep -f "$script" > /dev/null; then
            echo "  🟢  $script läuft (PID: $(pgrep -f "$script"))"
        else
            echo "  🔴  $script gestoppt"
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
        echo "Verwendung: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac