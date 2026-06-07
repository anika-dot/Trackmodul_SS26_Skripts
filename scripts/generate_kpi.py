'''
This module generates a kpi report and visualizations from the dobot log file.

Usage:
    python generate_kpi.py logs/dobot_log.jsonl
    python generate_kpi.py logs/dobot_log.jsonl
'''

import json
import argparse
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev
import pandas as pd
import matplotlib.pyplot as plt


COMPONENT_COLORS = {
    "controller": "#6E706E",
    "pickplace": "#BE5108",
    "sorter": "#4A8522",
}


def load_events(path):
    '''
    Loads events from a JSONL file, skipping invalid lines.
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
                continue
    return events


def extract_cycles(events):
    '''
    Extracts cycles from events by matching start and end conditions.
    
    New cycle starts at: action_start + action == pickplace_total
    Cycle ends at: run_finished
    '''

    cycles = []
    current_cycle = None

    for ev in events:
        event_type = ev.get("event")
        component = ev.get("component", "")
        action = ev.get("action", "")

        if (event_type == "action_start"and component == "controller" and action == "pickplace_total"):
            if current_cycle: 
                cycles.append(current_cycle)
                
            current_cycle = {
                "start_ts": ev["ts"],
                "pickplace_duration": None,
                "colorsensor_duration": None,
                "sorter_duration": None,
                "color": None,
                "status": "ok",
            }

        if not current_cycle:
            continue

        if (event_type == "action_end" and component == "controller"):
            if action == "pickplace_total":
                current_cycle["pickplace_duration"] = ev.get("duration_s")
            elif action == "colorsensor_total":
                current_cycle["colorsensor_duration"] = ev.get("duration_s")
            elif action == "sorter_total":
                current_cycle["sorter_duration"] = ev.get("duration_s")

            # error in any phase marks the whole cycle as error
            if ev.get("status") == "error":
                current_cycle["status"] = "error"

        # color detected event
        elif event_type == "color_detected":
            detected_color = ev.get("color")

            if detected_color:
                detected_color = detected_color.lower().strip()

            current_cycle["color"] = detected_color

        # cycle end
        elif event_type == "run_finished":
            current_cycle["end_ts"] = ev["ts"]
            current_cycle["total_duration"] = (ev["ts"] - current_cycle["start_ts"])

            cycles.append(current_cycle)
            current_cycle = None

    return cycles


def extract_action_intervals(events):
    '''
    Extract all action intervals by matching action_start and action_end events.
    '''
    open_actions = {}
    intervals = []

    for ev in events:
        if ev.get("event") == "action_start":
            key = (ev.get("component"), ev.get("action"))
            open_actions[key] = ev

        elif ev.get("event") == "action_end":
            key = (ev.get("component"), ev.get("action"))
            start_ev = open_actions.pop(key, None)
            if start_ev:
                intervals.append({
                    "component": ev.get("component"),
                    "action": ev.get("action"),
                    "start": start_ev["ts"],
                    "end": ev["ts"],
                    "duration": ev.get("duration_s", ev["ts"] - start_ev["ts"]),
                    "status": ev.get("status", "ok"),
                })

    return intervals


def extract_latencies(events, intervals):
    '''
    Extract various latency metrics from the event stream.
    '''''
    latencies = {
        "command_dispatch_pickplace": [],
        "command_dispatch_sorter": [],
        "inter_action": [],   
        "sensor_reaction": [],
        "task_handoff": [],
        "phase_overhead": [],
    }

    # Command dispatch latency (controller dispatch to pickplace receiving the task)
    pending_dispatch = None
    for ev in events:
        if (ev.get("event") == "action_start"
                and ev.get("component") == "controller"
                and ev.get("action") == "pickplace_total"):
            pending_dispatch = ev["ts"]
        elif (ev.get("event") == "task_received"
              and ev.get("component") == "pickplace"
              and pending_dispatch is not None):
            latencies["command_dispatch_pickplace"].append({
                "ts": ev["ts"],
                "latency": ev["ts"] - pending_dispatch,
            })
            pending_dispatch = None

    # Command dispatch latency (controller dispatch to sorter receiving the task)
    pending_dispatch = None
    for ev in events:
        if (ev.get("event") == "action_start"
                and ev.get("component") == "controller"
                and ev.get("action") == "sorter_total"):
            pending_dispatch = ev["ts"]
        elif (ev.get("event") == "sorter_start"
              and ev.get("component") == "sorter"
              and pending_dispatch is not None):
            latencies["command_dispatch_sorter"].append({
                "ts": ev["ts"],
                "latency": ev["ts"] - pending_dispatch,
            })
            pending_dispatch = None

    #Inter-action latency per component (action_end → next action_start in same component)
    by_component = defaultdict(list)
    for ev in events:
        if ev.get("event") in ("action_start", "action_end"):
            by_component[ev.get("component")].append(ev)

    for component, evs in by_component.items():
        evs_sorted = sorted(evs, key=lambda e: e["ts"])
        last_end = None
        for ev in evs_sorted:
            if ev["event"] == "action_end":
                last_end = ev
            elif ev["event"] == "action_start" and last_end is not None:
                gap = ev["ts"] - last_end["ts"]
                latencies["inter_action"].append({
                    "component": component,
                    "after_action": last_end.get("action"),
                    "before_action": ev.get("action"),
                    "ts": ev["ts"],
                    "latency": gap,
                })
                last_end = None

    # Sensor reaction latency (IR sensor or color detected → next action_start in same component)
    sensor_events = {"object_detected_by_ir_sensor", "color_detected"}
    pending_sensor = None
    for ev in events:
        if ev.get("event") in sensor_events:
            pending_sensor = ev
        elif (ev.get("event") == "action_start"
              and pending_sensor is not None
              and ev.get("component") == pending_sensor.get("component")):
            latencies["sensor_reaction"].append({
                "sensor_event": pending_sensor["event"],
                "next_action": ev.get("action"),
                "ts": ev["ts"],
                "latency": ev["ts"] - pending_sensor["ts"],
            })
            pending_sensor = None
    
    # Task handoff latency (task_finished → next component's action_start)
    pending_task_finished = None
    for ev in events:
        if ev.get("event") == "task_finished":
            pending_task_finished = ev
        elif (ev.get("event") == "action_start"
              and pending_task_finished is not None
              and ev.get("component") != pending_task_finished.get("component")):
            latencies["task_handoff"].append({
                "from_component": pending_task_finished.get("component"),
                "to_component": ev.get("component"),
                "ts": ev["ts"],
                "latency": ev["ts"] - pending_task_finished["ts"],
            })
            pending_task_finished = None

    # Phase overhead (*_total duration minus sum of sub-actions)
    total_intervals = [iv for iv in intervals if iv["action"].endswith("_total")]
    for total in total_intervals:
        component_name = total["action"].replace("_total", "")
        subs = [iv for iv in intervals
                if iv["component"] == component_name
                and total["start"] <= iv["start"] < total["end"]
                and not iv["action"].endswith("_total")]
        sub_sum = sum(iv["duration"] for iv in subs)
        overhead = total["duration"] - sub_sum
        latencies["phase_overhead"].append({
            "phase": total["action"],
            "total_duration": total["duration"],
            "sub_sum": sub_sum,
            "overhead": overhead,
        })

    return latencies


def compute_latency_stats(latencies):
    '''
    Compute statistics for latency metrics.
    '''
    stats = {}
    for name, entries in latencies.items():
        if name == "phase_overhead":
            values = [e["overhead"] for e in entries]
        else:
            values = [e["latency"] for e in entries]

        if not values:
            stats[name] = None
            continue

        stats[name] = {
            "count": len(values),
            "avg": mean(values),
            "min": min(values),
            "max": max(values),
            "p50": sorted(values)[len(values)//2],
            "p95": sorted(values)[int(len(values)*0.95)] if len(values) >= 20 else max(values),
            "std": stdev(values) if len(values) > 1 else 0,
        }
    return stats


def compute_kpis(cycles, intervals, events):
    ''''
    Compute KPI from the extracted cycles and intervals.
    '''

    # phase duration
    phase_durations = {
        "pickplace": [],
        "colorsensor": [],
        "sorter": [],
    }

    cycle_totals = []
    colors = defaultdict(int)
    errors = 0

    for cycle in cycles:
        if cycle["pickplace_duration"]:
            phase_durations["pickplace"].append(cycle["pickplace_duration"])
        if cycle["colorsensor_duration"]:
            phase_durations["colorsensor"].append(cycle["colorsensor_duration"])
        if cycle["sorter_duration"]:
            phase_durations["sorter"].append(cycle["sorter_duration"])
        if cycle.get("total_duration"):
            cycle_totals.append(cycle["total_duration"])
        if cycle.get("color"):
            colors[cycle["color"]] += 1
        if cycle.get("status") == "error":
            errors += 1

    # compute basic statistics
    def calc_stats(values):
        if not values:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "std": 0, "total": 0}
        return {
            "count": len(values),
            "avg": mean(values),
            "min": min(values),
            "max": max(values),
            "std": stdev(values) if len(values) > 1 else 0,
            "total": sum(values),
        }

    # action statistics (for detailed analysis)
    action_durations = defaultdict(list)
    for iv in intervals:
        action_durations[iv["action"]].append(iv["duration"])

    action_stats = {
        action: calc_stats(durations)
        for action, durations in action_durations.items()
    }

    success_rate = ((len(cycles) - errors) / len(cycles) * 100) if cycles else 0

    latencies = extract_latencies(events, intervals)
    latency_stats = compute_latency_stats(latencies)

    return {
        "total_cycles": len(cycles),
        "total_runtime": sum(cycle_totals),
        "cycle_stats": calc_stats(cycle_totals),
        "phase_stats": {
            phase: calc_stats(durations)
            for phase, durations in phase_durations.items()
        },
        "action_stats": action_stats,
        "color_distribution": dict(colors),
        "success_rate": success_rate,
        "errors": errors,
        "cycles": cycles,
        "intervals": intervals,
        "latencies": latencies,
        "latency_stats": latency_stats
    }


def print_report(kpis):
    '''
    Print a formatted KPI report to the console.
    '''
    print("\n" + "=" * 60)
    print("                    KPI REPORT")
    print("=" * 60)

    print(f"\n Overview")
    print(f"   Number of cycles:         {kpis['total_cycles']}")
    print(f"   Total runtime:            {kpis['total_runtime']:.2f} s "
          f"({kpis['total_runtime']/60:.2f} min)")
    print(f"   Success rate:             {kpis['success_rate']:.1f}%")
    print(f"   Errors:                   {kpis['errors']}")

    print(f"\n Cycle times")
    cs = kpis["cycle_stats"]
    print(f"   Ø per cycle:              {cs['avg']:.2f} s")
    print(f"   Min / Max:                {cs['min']:.2f} s / {cs['max']:.2f} s")
    print(f"   Standard deviation:       {cs['std']:.2f} s")

    print(f"\n Phase durations")
    for phase, stats in kpis["phase_stats"].items():
        if stats["count"] > 0:
            print(f"   {phase:20s}  Ø {stats['avg']:6.2f} s  "
                  f"(min {stats['min']:.2f}, max {stats['max']:.2f}, "
                  f"σ {stats['std']:.2f})")

    print(f"\n Color distribution")
    for color, count in sorted(kpis["color_distribution"].items(),
                               key=lambda x: -x[1]):
        pct = count / kpis["total_cycles"] * 100 if kpis["total_cycles"] else 0
        print(f"   {color:15s}  {count:3d}  ({pct:5.1f}%)")

    print(f"\n Latency metrics")
    for name, stats in kpis["latency_stats"].items():
        if stats:
            print(f"   {name:30s}  Ø {stats['avg']*1000:6.2f} ms  "
                  f"(min {stats['min']*1000:.2f} ms, max {stats['max']*1000:.2f} ms, "
                  f"σ {stats['std']*1000:.2f} ms)")

    print("\n" + "=" * 60)


def plot_cycle_durations(kpis, outdir):
    '''
    Line plot of cycle durations, showing each cycle and the average duration as a dashed line.
    '''
    cycles = kpis["cycles"]
    durations = [c.get("total_duration", 0) for c in cycles if c.get("total_duration")]

    if not durations:
        return

    plt.figure(figsize=(12, 5))
    plt.plot(range(1, len(durations) + 1), durations, marker="o", linewidth=1, markersize=4)
    plt.axhline(mean(durations), color="red", linestyle="--", label=f"Ø {mean(durations):.2f}s")
    plt.xlabel("Cycle")
    plt.ylabel("Duration [s]")
    plt.title("Duration per Cycle")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    path = outdir / "cycle_durations.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def plot_phase_comparison(kpis, outdir):
    '''
    Bar chart: Comparison of phase durations.
    '''
    phases = []
    avgs = []
    stds = []

    for phase in ["pickplace", "colorsensor", "sorter"]:
        stats = kpis["phase_stats"].get(phase, {})
        if stats.get("count", 0) > 0:
            phases.append(phase)
            avgs.append(stats["avg"])
            stds.append(stats["std"])

    if not phases:
        return

    plt.figure(figsize=(10, 5))
    bars = plt.bar(phases, avgs, yerr=stds, capsize=5, color=["#BE5108", "#D89900", "#4A8522"])
    plt.ylabel("Duration [s]")
    plt.title("Average Duration per Phase")
    plt.grid(axis="y", alpha=0.3)

    for bar, avg in zip(bars, avgs):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f"{avg:.2f}s", ha="center", va="bottom", fontsize=10)

    plt.tight_layout()
    path = outdir / "phase_comparison.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def plot_phase_breakdown(kpis, outdir):
    '''
    Stacked bar chart: Time distribution per cycle.
    '''
    cycles = kpis["cycles"]

    pickplace = [c.get("pickplace_duration", 0) or 0 for c in cycles]
    colorsensor = [c.get("colorsensor_duration", 0) or 0 for c in cycles]
    sorter = [c.get("sorter_duration", 0) or 0 for c in cycles]

    x = range(1, len(cycles) + 1)

    plt.figure(figsize=(14, 6))
    plt.bar(x, pickplace, label="Pickplace", color="#BE5108")
    plt.bar(x, colorsensor, bottom=pickplace, label="Colorsensor", color="#D89900")
    plt.bar(x, sorter, bottom=[p + c for p, c in zip(pickplace, colorsensor)],
            label="Sorter", color="#4A8522")

    plt.xlabel("Cycle")
    plt.ylabel("Duration [s]")
    plt.title("Time Distribution per Cycle")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    path = outdir / "phase_breakdown.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def plot_color_distribution(kpis, outdir):
    '''
    Pie chart of the color distribution.
    '''
    colors = kpis["color_distribution"]

    
    # None entfernen
    colors = {
    k: v for k, v in colors.items()
    if k not in (None, "", "unknown")
    }

    if not colors:
        return

    labels = [str(c) for c in colors.keys()]
    values = list(colors.values())

    color_map = {
        "blue": "#1a80bb",
        "other": "#b8b8b8",
    }
    pie_colors = [color_map.get(l, "#bdc3c7") for l in labels]

    plt.figure(figsize=(8, 8))
    plt.pie(values, labels=labels, autopct="%1.1f%%", colors=pie_colors,
            startangle=90, explode=[0.02] * len(labels))
    plt.title("Detected Colors")

    path = outdir / "color_distribution.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def plot_action_boxplot(kpis, outdir):
    '''
    Boxplot of all actions.
    '''
    intervals = kpis["intervals"]
    by_action = defaultdict(list)

    for iv in intervals:
        by_action[iv["action"]].append(iv["duration"])

    # sort actions by average duration for better visualization
    sorted_actions = sorted(by_action.keys(), key=lambda a: mean(by_action[a]), reverse=True)
    values = [by_action[a] for a in sorted_actions]

    plt.figure(figsize=(14, 8))
    plt.boxplot(values, vert=False, tick_labels=sorted_actions)
    plt.xlabel("Duration [s]")
    plt.title("Distribution of Action Durations")
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()

    path = outdir / "action_boxplot.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def plot_gantt(kpis, outdir):
    '''
    Gantt chart of all action intervals.
    '''
    intervals = kpis["intervals"]
    if not intervals:
        return

    t0 = min(iv["start"] for iv in intervals)
    components = sorted({iv["component"] for iv in intervals})
    y_pos = {c: i for i, c in enumerate(components)}
    fig, ax = plt.subplots(figsize=(14, 1.2 + len(components)))

    for iv in intervals:
        duration = iv["duration"]
        ax.barh(
            y=y_pos[iv["component"]],
            width=max(duration, 0.05),
            left=iv["start"] - t0,
            height=0.6,
            color=COMPONENT_COLORS.get(iv["component"], "gray"),
            edgecolor="black",
            linewidth=0.5,
        )
        ax.text(
            iv["start"] - t0 + duration / 2,
            y_pos[iv["component"]],
            f"{iv['action']}",
            ha="center",
            va="center",
            fontsize=7,
            color="white",
            clip_on=True,
        )
    ax.set(
        yticks=list(y_pos.values()),
        yticklabels=list(y_pos.keys()),
        xlabel="Time since start [s]",
        title="Gantt Chart",
    )
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    plt.tight_layout()
    path = outdir / "gantt_chart.png"
    plt.savefig(path, dpi=150)
    plt.close()

    print(f"   → {path}")


def plot_latencies(latencies, outdir):
    '''
    Boxplot of latency metrics.
    '''
    data = []
    labels = []
    for name, entries in latencies.items():
        if name == "phase_overhead":
            values = [e["overhead"] for e in entries]
        else:
            values = [e["latency"] * 1000 for e in entries]  # in ms
        if values:
            data.append(values)
            labels.append(name)

    if not data:
        return

    plt.figure(figsize=(12, 6))
    plt.boxplot(data, tick_labels=labels, vert=False)
    plt.xlabel("Latency [ms]")
    plt.title("Latency Distribution")
    plt.grid(axis="x", alpha=0.3)
    plt.xscale("log")  # log scale for better visibility of small latencies
    plt.tight_layout()
    path = outdir / "latencies.png"
    plt.savefig(path, dpi=150)
    plt.close()

    print(f"   → {path}")   


def export_csv(kpis, outdir):
    '''
    Export cycles and intervals as CSV files for further analysis.
    '''
    # Cycles
    df_cycles = pd.DataFrame(kpis["cycles"])
    path_cycles = outdir / "cycles.csv"
    df_cycles.to_csv(path_cycles, index=False)
    print(f"   → {path_cycles}")

    # Intervals
    df_intervals = pd.DataFrame(kpis["intervals"])
    path_intervals = outdir / "intervals.csv"
    df_intervals.to_csv(path_intervals, index=False)
    print(f"   → {path_intervals}")


def main():
    '''
    Main function to parse arguments, load data, compute KPIs, and generate report and visualizations.
    '''
    parser = argparse.ArgumentParser(description="KPI-Report for Dobot-Logs")
    parser.add_argument("logfile", help="Path to the JSONL log file")
    parser.add_argument("--output-dir", "-o", default="report",
                        help="Output directory (default: report)")

    args = parser.parse_args()
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\n load log: {args.logfile}")
    events = load_events(args.logfile)
    print(f"   {len(events)} events loaded")

    cycles = extract_cycles(events)
    intervals = extract_action_intervals(events)
    print(f"   {len(cycles)} cycles detected")
    print(f"   {len(intervals)} action intervals")

    kpis = compute_kpis(cycles, intervals, events)
    print_report(kpis)

    plot_cycle_durations(kpis, outdir)
    plot_phase_comparison(kpis, outdir)
    plot_phase_breakdown(kpis, outdir)
    plot_color_distribution(kpis, outdir)
    plot_action_boxplot(kpis, outdir)
    plot_gantt(kpis, outdir)
    plot_latencies(kpis["latencies"], outdir)
    export_csv(kpis, outdir)

    print(f"\n Report created in: {outdir.absolute()}\n")


if __name__ == "__main__":
    main()