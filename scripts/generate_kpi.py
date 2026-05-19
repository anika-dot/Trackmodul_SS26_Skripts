"""
generate kpi report and visualizations from the dobot log file

Usage:
    python generate_kpi.py logs/dobot_log.jsonl
    python generate_kpi.py logs/dobot_log.jsonl
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev

import pandas as pd
import matplotlib.pyplot as plt

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
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                print("Ungültige JSON-Zeile übersprungen")
    return events


def split_runs(events):
    '''
    Split the events into runs based on "run_started" and "run_finished" events.
    '''
    runs = []
    current = []

    for ev in events:
        if ev.get("event") == "run_started":
            current = [ev]
        elif current:
            current.append(ev)
            if ev.get("event") == "run_finished":
                runs.append(current)
                current = []
    return runs


def build_intervals(events):
    '''
    Generate intervals for each action by matching start and end events.
    '''
    open_actions = {}
    intervals = []

    for ev in events:
        if ev.get("event") == "action_start":
            key = (
                ev["component"],
                ev["action"]
            )
            open_actions[key] = ev

        elif ev.get("event") == "action_end":
            key = (
                ev["component"],
                ev["action"]
            )

            start_ev = open_actions.pop(key, None)
            if start_ev is None:
                continue

            intervals.append({
                "component": ev["component"],
                "action": ev["action"],
                "start": start_ev["ts"],
                "end": ev["ts"],
                "duration": ev.get(
                    "duration_s",
                    ev["ts"] - start_ev["ts"]
                ),
                "status": ev.get("status", "unknown"),
            })

    return intervals


def compute_kpis(runs):
    '''
    Compute KPIs from the runs:
    - Average duration of each action
    - Success rate of actions
    - Distribution of detected colors
    - MQTT latency for pickplace actions
    '''
    all_intervals = []
    run_durations = []
    colors = defaultdict(int)
    mqtt_latencies = []

    for run_idx, run in enumerate(runs):
        intervals = build_intervals(run)
        for iv in intervals:
            iv["run"] = run_idx + 1
        all_intervals.extend(intervals)

        # Run-duration
        start = run[0]["ts"]
        end = run[-1]["ts"]
        run_durations.append(end - start)

        # color distribution
        for ev in run:
            if ev.get("event") == "color_detected":
                colors[ev.get("color", "unknown")] += 1

        # MQTT-Latency
        action_end_ts = None

        for ev in run:
            if (
                ev.get("event") == "task_finished"
                and ev.get("component") == "pickplace"
            ):
                action_end_ts = ev["ts"]
            if (
                action_end_ts
                and ev.get("event") == "mqtt_received"
                and "pickplace/status" in ev.get("topic", "")
            ):
                mqtt_latencies.append(ev["ts"] - action_end_ts)
                action_end_ts = None

    # Action-Stats
    by_action = defaultdict(list)

    for iv in all_intervals:
        by_action[iv["action"]].append(iv["duration"])

    action_stats = {}

    for action, durations in by_action.items():
        action_stats[action] = {
            "count": len(durations),
            "avg": mean(durations),
            "min": min(durations),
            "max": max(durations),
            "std": stdev(durations) if len(durations) > 1 else 0.0,
        }

    # Error-rate
    total_actions = len(all_intervals)

    failed_actions = sum(
        1 for iv in all_intervals
        if iv["status"] == "error"
)

    success_rate = (
        (total_actions - failed_actions)
        / total_actions * 100
    ) if total_actions else 0

    return {
        "runs": len(runs),
        "run_durations": run_durations,
        "mqtt_latencies": mqtt_latencies,
        "color_distribution": dict(colors),
        "success_rate": success_rate,
        "intervals": all_intervals,
        "action_stats": action_stats,
    }


def print_report(kpis):
    '''
    Print a concise KPI report to the console.
    '''
    print("\n================ KPI REPORT ================\n")
    print(f"Runs:                    {kpis['runs']}")
    print(f"Ø Run Duration:             "
        f"{mean(kpis['run_durations']):.2f}s")

    print(f"Success Rate:             "
        f"{kpis['success_rate']:.2f}%")

    if kpis["mqtt_latencies"]:
        print(f"Ø MQTT-Latency:           "
            f"{mean(kpis['mqtt_latencies']):.3f}s")

    print("\n----------- Actions -----------")
    for action, s in sorted(
        kpis["action_stats"].items(),
        key=lambda x: x[1]["avg"],
        reverse=True):
        print(f"{action:40s} "
            f"avg={s['avg']:6.2f}s "
            f"std={s['std']:5.2f}s "
            f"max={s['max']:6.2f}s")


def plot_action_averages(kpis, outdir):
    '''
    Bar chart of the average duration of each action to identify bottlenecks.
    '''
    stats = kpis["action_stats"]
    actions = list(stats.keys())
    averages = [
        stats[a]["avg"]
        for a in actions
    ]

    plt.figure(figsize=(12, 6))
    plt.barh(actions, averages)
    plt.xlabel("Average duration [s]")
    plt.title("Average duration of each action")
    plt.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()
    path = outdir / "action_averages.png"
    plt.savefig(path, dpi=150)

    print(f"Saved: {path}")


def plot_run_durations(kpis, outdir):
    '''
    Line plot of the run durations to show the trend over multiple runs.
    '''
    durations = kpis["run_durations"]
    runs = list(range(1, len(durations) + 1))

    plt.figure(figsize=(10, 5))
    plt.plot(runs, durations, marker="o")
    plt.xlabel("Run")
    plt.ylabel("Duration [s]")
    plt.title("Duration of each run")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    path = outdir / "run_durations.png"
    plt.savefig(path, dpi=150)

    print(f"Saved: {path}")

def plot_boxplot_actions(kpis, outdir):
    '''
    Boxplot of the action durations to show the distribution and outliers.
    '''
    intervals = kpis["intervals"]
    by_action = defaultdict(list)

    for iv in intervals:
        by_action[iv["action"]].append(iv["duration"])

    labels = list(by_action.keys())
    values = [by_action[a] for a in labels]

    plt.figure(figsize=(14, 6))
    plt.boxplot(values, tick_labels=labels, vert=False)
    plt.xlabel("Duration [s]")
    plt.title("Distribution of the action durations")
    plt.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()

    path = outdir / "action_boxplot.png"
    plt.savefig(path, dpi=150)

    print(f"Saved: {path}")



def plot_color_distribution(kpis, outdir):
    '''
    Pie chart of the detected colors by the color sensor.
    '''
    colors = kpis["color_distribution"]

    if not colors:
        return

    labels = list(colors.keys())
    values = list(colors.values())

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Color Distribution")

    path = outdir / "color_distribution.png"
    plt.savefig(path, dpi=150)

    print(f"Saved: {path}")



def export_csv(kpis, outdir):
    '''
    Export of the action intervals as CSV for further analysis.
    '''
    df = pd.DataFrame(kpis["intervals"])
    path = outdir / "intervals.csv"
    df.to_csv(path, index=False)

    print(f"CSV saved: {path}")


def main():
    '''
    Main function to execute the script.
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument("logfile", help="Path to the JSONL file")
    parser.add_argument("--output-dir", "-o", default="report", help="Output directory")

    args = parser.parse_args()
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    events = load_events(args.logfile)
    runs = split_runs(events)
    kpis = compute_kpis(runs)
    print_report(kpis)
    export_csv(kpis, outdir)
    plot_action_averages(kpis, outdir)
    plot_run_durations(kpis, outdir)
    plot_boxplot_actions(kpis, outdir)
    plot_color_distribution(kpis, outdir)
    print("\nReport generated.")


if __name__ == "__main__":
    main()
    