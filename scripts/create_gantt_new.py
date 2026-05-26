"""
generate_gantt.py
Liest eine JSONL-Logdatei und erzeugt einen Gantt-Chart der Aktionen pro Komponente.

Verwendung:
    python generate_gantt.py logs/dobot_log_2025-01-15.jsonl
    python generate_gantt.py logs/dobot_log_2025-01-15.jsonl --output gantt.png
"""

import json
import sys
import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent  # scripts/ → project_root/
LOG_DIR = ROOT_DIR / "logs"

BAR_HEIGHT = 0.6
MIN_BAR_WIDTH = 0.05   # Damit auch 0s-Aktionen sichtbar sind
FIG_WIDTH = 12
FIG_HEIGHT_BASE = 1.2
FIG_HEIGHT_PER_ROW = 0.8
LABEL_FONT_SIZE = 8
SUMMARY_FONT_SIZE = 9


# ---------------------------------------------------------------------------
# Daten laden & verarbeiten
# ---------------------------------------------------------------------------

def load_events(path: Path | str) -> list[dict]:
    """
    Liest eine JSONL-Datei ein.

    Args:
        path: Pfad zur .jsonl Datei
    Returns:
        Liste von Event-Dicts mit keys: ts, event, component, action
    """
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def build_intervals(events: list[dict]) -> list[dict]:
    """
    Wandelt action_start/action_end-Paare in Intervalle um.

    Args:
        events: Liste von Event-Dicts aus load_events()
    Returns:
        Liste von Intervall-Dicts mit keys: component, action, start, end, duration
    """
    open_actions: dict[tuple, float] = {}  # (component, action) -> start_ts
    intervals = []

    for ev in events:
        key = (ev["component"], ev["action"])

        if ev.get("event") == "action_start":
            open_actions[key] = ev["ts"]

        elif ev.get("event") == "action_end":
            start_ts = open_actions.pop(key, None)
            if start_ts is None:
                # Ende ohne Start – könnte aus einem vorherigen Run stammen
                continue
            intervals.append({
                "component": ev["component"],
                "action":    ev["action"],
                "start":     start_ts,
                "end":       ev["ts"],
                "duration":  ev["ts"] - start_ts,
            })

    # Warnung bei fehlenden action_end-Events
    for component, action in open_actions:
        print(f"  Warnung: Kein action_end für {component}/{action}")

    return intervals


# ---------------------------------------------------------------------------
# Gantt-Chart zeichnen (aufgeteilt in Hilfsfunktionen)
# ---------------------------------------------------------------------------

def _build_color_map(components: list[str]) -> dict[str, tuple]:
    """Weist jeder Komponente eine Farbe aus der tab10-Palette zu."""
    cmap = plt.get_cmap("tab10")
    return {comp: cmap(i % 10) for i, comp in enumerate(components)}


def _create_figure(num_components: int):
    """Erstellt Figure und Axes mit zur Komponentenanzahl passender Größe."""
    height = FIG_HEIGHT_BASE + FIG_HEIGHT_PER_ROW * num_components
    return plt.subplots(figsize=(FIG_WIDTH, height))


def _draw_bars(ax, intervals: list[dict], comp_y: dict, comp_color: dict, t0: float) -> None:
    """Zeichnet die Balken und Beschriftungen in den Axes."""
    for iv in intervals:
        y = comp_y[iv["component"]]
        x_start = iv["start"] - t0
        width = max(iv["duration"], MIN_BAR_WIDTH)

        ax.barh(
            y=y, width=width, left=x_start, height=BAR_HEIGHT,
            color=comp_color[iv["component"]],
            edgecolor="black", linewidth=0.5,
        )

        label = f"{iv['action']} ({iv['duration']:.1f}s)"
        ax.text(
            x_start + width / 2, y, label,
            ha="center", va="center",
            fontsize=LABEL_FONT_SIZE, color="white",
            clip_on=True,
        )


def _style_axes(ax, comp_y: dict, total: float) -> None:
    """Setzt Achsenbeschriftungen, Grid und Gesamtdauer-Annotation."""
    ax.set_yticks(list(comp_y.values()))
    ax.set_yticklabels(list(comp_y.keys()))
    ax.set_xlabel("Zeit seit Start (Sekunden)")
    ax.set_title("Dobot-System: Gantt-Chart")
    ax.invert_yaxis()  # Erste Komponente oben
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    ax.text(
        0.99, 0.02, f"Gesamtdauer: {total:.1f}s",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=SUMMARY_FONT_SIZE,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )


def plot_gantt(intervals: list[dict], output: str | None = None) -> None:
    """
    Erstellt und speichert (oder zeigt) den Gantt-Chart.

    Args:
        intervals: Ausgabe von build_intervals()
        output:    Pfad zum Speichern des Bildes. None → plt.show()
    """
    if not intervals:
        print("Keine Aktions-Intervalle in der Logdatei gefunden.")
        return

    t0 = min(iv["start"] for iv in intervals)
    total = max(iv["end"] for iv in intervals) - t0

    components = sorted({iv["component"] for iv in intervals})
    comp_y = {comp: i for i, comp in enumerate(components)}
    comp_color = _build_color_map(components)

    fig, ax = _create_figure(len(components))
    _draw_bars(ax, intervals, comp_y, comp_color, t0)
    _style_axes(ax, comp_y, total)
    plt.tight_layout()

    if output:
        plt.savefig(output, dpi=150)
        print(f"Gantt-Chart gespeichert: {output}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Konsolenauswertung
# ---------------------------------------------------------------------------

def print_summary(intervals: list[dict]) -> None:
    """Gibt eine kurze Statistik pro Komponente auf der Konsole aus."""
    if not intervals:
        return

    print("\n=== Auswertung ===")
    by_component: dict[str, list[float]] = defaultdict(list)
    for iv in intervals:
        by_component[iv["component"]].append(iv["duration"])

    for comp, durations in by_component.items():
        print(
            f"  {comp:12s}  Aktionen: {len(durations):3d}   "
            f"Σ={sum(durations):6.2f}s   "
            f"⌀={sum(durations) / len(durations):5.2f}s   "
            f"max={max(durations):5.2f}s"
        )

    total = max(iv["end"] for iv in intervals) - min(iv["start"] for iv in intervals)
    print(f"  Gesamtdauer (Wallclock): {total:.2f}s\n")


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Gantt-Chart aus Dobot-Logs erstellen.")
    parser.add_argument("logfile", help="Pfad zur .jsonl Logdatei")
    parser.add_argument("--output", "-o", help="Bildpfad (z.B. gantt.png). Ohne diesen Parameter wird nur angezeigt.")
    args = parser.parse_args()

    log_path = Path(args.logfile)
    if not log_path.exists():
        sys.exit(f"Fehler: Logdatei nicht gefunden: {log_path}")

    events = load_events(log_path)
    if not events:
        sys.exit("Fehler: Logdatei ist leer.")

    intervals = build_intervals(events)
    print_summary(intervals)
    plot_gantt(intervals, output=args.output)


if __name__ == "__main__":
    main()