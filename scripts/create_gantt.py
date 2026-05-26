'''
creates a gantt chart from the dobot log file, showing the timing of actions per component.

Usage:
    python create_gantt.py logs/dobot_log_2025-01-15.jsonl
    python create_gantt.py logs/dobot_log_2025-01-15.jsonl --output gantt.png
'''

import json
import sys
import argparse
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent 
LOG_DIR = ROOT_DIR / "logs"


def load_events(path):
    '''
    Load events from a JSONL file, skipping invalid lines.
    '''
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def build_intervals(events):
    '''
    Generate intervals for each action by matching start and end events.
    '''
    open_actions = {} 
    intervals = []

    for ev in events:
        if ev.get("event") == "action_start":
            key = (ev["component"], ev["action"])
            open_actions[key] = ev["ts"]
        elif ev.get("event") == "action_end":
            key = (ev["component"], ev["action"])
            start_ts = open_actions.pop(key, None)
            if start_ts is None:
                # end without a start - ignore this event
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
    '''
    Create a Gantt chart from the intervals, showing actions per component over time.
    '''
    if not intervals:
        print("No action intervals found in the log file.")
        return

    t0 = min(iv["start"] for iv in intervals)

    components = sorted({iv["component"] for iv in intervals})
    comp_y = {c: i for i, c in enumerate(components)}

    # one color per component, cycling through a colormap
    cmap = plt.get_cmap("tab10")
    comp_color = {c: cmap(i % 10) for i, c in enumerate(components)}

    fig, ax = plt.subplots(figsize=(12, 1.2 + 0.8 * len(components)))

    for iv in intervals:
        y = comp_y[iv["component"]]
        x_start = iv["start"] - t0
        width = max(iv["duration"], 0.05)  # min width for visibility
        ax.barh(
            y=y, width=width, left=x_start, height=0.6,
            color=comp_color[iv["component"]],
            edgecolor="black", linewidth=0.5,
        )
        
        label = f"{iv['action']} ({iv['duration']:.1f}s)"
        ax.text(
            x_start + width / 2, y, label,
            ha="center", va="center", fontsize=8, color="white",
            clip_on=True,
        )

    ax.set_yticks(list(comp_y.values()))
    ax.set_yticklabels(list(comp_y.keys()))
    ax.set_xlabel("Time since start (seconds)")
    ax.set_title("Dobot-system: gantt-chart")
    ax.invert_yaxis()  # first component on top
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    # Total duration as info
    total = max(iv["end"] for iv in intervals) - t0
    ax.text(
        0.99, 0.02, f"Total duration: {total:.1f}s",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=9, bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.tight_layout()
    print(output)
    if output:
        plt.savefig(output, dpi=150)
        print(f"Gantt-chart saved: {output}")
    else:
        plt.show()


def print_summary(intervals):
    '''
    print a summary of the actions per component, showing count, total duration, average duration, and max duration.
    '''
    if not intervals:
        return
    print("\n=== Results ===")
    by_component = defaultdict(list)
    for iv in intervals:
        by_component[iv["component"]].append(iv["duration"])

    for comp, durations in by_component.items():
        print(f"  {comp:12s}  Actions: {len(durations):3d}   "
              f"Σ={sum(durations):6.2f}s   "
              f"⌀={sum(durations)/len(durations):5.2f}s   "
              f"max={max(durations):5.2f}s")
    total = max(iv["end"] for iv in intervals) - min(iv["start"] for iv in intervals)
    print(f"  Total duration (Wallclock): {total:.2f}s\n")


def main():
    '''
    Main function to parse arguments, load events, build intervals, print summary, and plot Gantt chart.
    '''
    parser = argparse.ArgumentParser(description="Create a Gantt chart from Dobot log files.")
    parser.add_argument("logfile", help="Path to the .jsonl log file")
    parser.add_argument("--output", "-o", help="Image path (e.g., gantt.png). If not specified, the chart will be displayed.")
    args = parser.parse_args()
    print(parser)

    events = load_events(args.logfile)
    intervals = build_intervals(events)
    print_summary(intervals)
    plot_gantt(intervals, output=args.output)


if __name__ == "__main__":
    main()
