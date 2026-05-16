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
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def load_events(path):
    """Liest JSONL ein und gibt eine Liste von Records zurück."""
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def build_intervals(events):
    """
    Wandelt action_start/action_end-Paare in Intervalle um.
    Gibt zurück: list of (component, action, start_ts, end_ts)
    """
    open_actions = {}  # (component, action) -> start_ts
    intervals = []

    for ev in events:
        if ev.get("event") == "action_start":
            key = (ev["component"], ev["action"])
            open_actions[key] = ev["ts"]
        elif ev.get("event") == "action_end":
            key = (ev["component"], ev["action"])
            start_ts = open_actions.pop(key, None)
            if start_ts is None:
                # Ende ohne Start - überspringen, könnte aus vorherigem Run sein
                continue
            intervals.append({
                "component": ev["component"],
                "action": ev["action"],
                "start": start_ts,
                "end": ev["ts"],
                "duration": ev["ts"] - start_ts,
            })

    return intervals


def plot_gantt(intervals, output=None):
    if not intervals:
        print("Keine Aktions-Intervalle in der Logdatei gefunden.")
        return

    # Zeit-Nullpunkt = frühestes Event
    t0 = min(iv["start"] for iv in intervals)

    # Komponenten sortieren - jede bekommt eine eigene Y-Zeile
    components = sorted({iv["component"] for iv in intervals})
    comp_y = {c: i for i, c in enumerate(components)}

    # Farbe pro Komponente (für ein klares visuelles Mapping)
    cmap = plt.get_cmap("tab10")
    comp_color = {c: cmap(i % 10) for i, c in enumerate(components)}

    fig, ax = plt.subplots(figsize=(12, 1.2 + 0.8 * len(components)))

    for iv in intervals:
        y = comp_y[iv["component"]]
        x_start = iv["start"] - t0
        width = max(iv["duration"], 0.05)  # Mini-Breite, damit auch 0s-Aktionen sichtbar sind
        ax.barh(
            y=y, width=width, left=x_start, height=0.6,
            color=comp_color[iv["component"]],
            edgecolor="black", linewidth=0.5,
        )
        # Beschriftung im Balken (oder daneben, wenn er zu schmal ist)
        label = f"{iv['action']} ({iv['duration']:.1f}s)"
        ax.text(
            x_start + width / 2, y, label,
            ha="center", va="center", fontsize=8, color="white",
            clip_on=True,
        )

    ax.set_yticks(list(comp_y.values()))
    ax.set_yticklabels(list(comp_y.keys()))
    ax.set_xlabel("Zeit seit Start (Sekunden)")
    ax.set_title("Dobot-System: Gantt-Chart")
    ax.invert_yaxis()  # Erste Komponente oben
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    # Gesamtdauer als Info
    total = max(iv["end"] for iv in intervals) - t0
    ax.text(
        0.99, 0.02, f"Gesamtdauer: {total:.1f}s",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=9, bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.tight_layout()

    if output:
        plt.savefig(output, dpi=150)
        print(f"Gantt-Chart gespeichert: {output}")
    else:
        plt.show()


def print_summary(intervals):
    """Kurze Statistik in der Konsole."""
    if not intervals:
        return
    print("\n=== Auswertung ===")
    by_component = defaultdict(list)
    for iv in intervals:
        by_component[iv["component"]].append(iv["duration"])

    for comp, durations in by_component.items():
        print(f"  {comp:12s}  Aktionen: {len(durations):3d}   "
              f"Σ={sum(durations):6.2f}s   "
              f"⌀={sum(durations)/len(durations):5.2f}s   "
              f"max={max(durations):5.2f}s")
    total = max(iv["end"] for iv in intervals) - min(iv["start"] for iv in intervals)
    print(f"  Gesamtdauer (Wallclock): {total:.2f}s\n")


def main():
    parser = argparse.ArgumentParser(description="Gantt-Chart aus Dobot-Logs erstellen.")
    parser.add_argument("logfile", help="Pfad zur .jsonl Logdatei")
    parser.add_argument("--output", "-o", help="Bildpfad (z.B. gantt.png). Ohne diesen Parameter wird nur angezeigt.")
    args = parser.parse_args()

    events = load_events(args.logfile)
    intervals = build_intervals(events)
    print_summary(intervals)
    plot_gantt(intervals, output=args.output)


if __name__ == "__main__":
    main()
