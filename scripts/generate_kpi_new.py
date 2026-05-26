"""
KPI-Report für Dobot-Logs (neues Format)

Usage:
    python generate_kpi.py logs/dobot_log.jsonl
    python generate_kpi.py logs/dobot_log.jsonl -o report
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev

import pandas as pd
import matplotlib.pyplot as plt


def load_events(path):
    """Lädt Events aus JSONL-Datei."""
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
    """
    Extrahiert Durchgänge (Cycles) basierend auf run_started/run_finished.
    Jeder Cycle enthält: pickplace_total, colorsensor_total, sorter_total.
    """
    cycles = []
    current_cycle = None
    phase_starts = {}

    for ev in events:
        event_type = ev.get("event")
        component = ev.get("component", "")
        action = ev.get("action", "")

        # Neuer Durchgang startet
        if event_type == "run_started":
            current_cycle = {
                "start_ts": ev["ts"],
                "pickplace_duration": None,
                "colorsensor_duration": None,
                "sorter_duration": None,
                "color": None,
                "status": "ok",
            }
            phase_starts = {}

        # Phase startet (controller trackt die _total actions)
        elif event_type == "action_start" and component == "controller":
            if action in ("pickplace_total", "colorsensor_total", "sorter_total"):
                phase_starts[action] = ev["ts"]

        # Phase endet
        elif event_type == "action_end" and component == "controller":
            if action == "pickplace_total" and current_cycle:
                current_cycle["pickplace_duration"] = ev.get("duration_s")
            elif action == "colorsensor_total" and current_cycle:
                current_cycle["colorsensor_duration"] = ev.get("duration_s")
            elif action == "sorter_total" and current_cycle:
                current_cycle["sorter_duration"] = ev.get("duration_s")

            # Fehler-Status prüfen
            if ev.get("status") == "error" and current_cycle:
                current_cycle["status"] = "error"

        # Farbe erkannt
        elif event_type == "color_detected" and current_cycle:
            current_cycle["color"] = ev.get("color")

        # Durchgang beendet
        elif event_type == "run_finished" and current_cycle:
            current_cycle["end_ts"] = ev["ts"]
            current_cycle["total_duration"] = ev["ts"] - current_cycle["start_ts"]
            cycles.append(current_cycle)
            current_cycle = None

    return cycles


def extract_action_intervals(events):
    """Extrahiert alle Aktionsintervalle für detaillierte Analyse."""
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


def compute_kpis(cycles, intervals):
    """Berechnet KPIs aus Cycles und Intervallen."""

    # Phasen-Statistiken
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

    # Statistiken berechnen
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

    # Aktions-Statistiken (für detaillierte Analyse)
    action_durations = defaultdict(list)
    for iv in intervals:
        action_durations[iv["action"]].append(iv["duration"])

    action_stats = {
        action: calc_stats(durations)
        for action, durations in action_durations.items()
    }

    success_rate = ((len(cycles) - errors) / len(cycles) * 100) if cycles else 0

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
    }


def print_report(kpis):
    """Gibt KPI-Report auf der Konsole aus."""
    print("\n" + "=" * 60)
    print("                    KPI REPORT")
    print("=" * 60)

    print(f"\n📊 ÜBERSICHT")
    print(f"   Durchgänge (Cycles):      {kpis['total_cycles']}")
    print(f"   Gesamtlaufzeit:           {kpis['total_runtime']:.2f} s "
          f"({kpis['total_runtime']/60:.2f} min)")
    print(f"   Erfolgsrate:              {kpis['success_rate']:.1f}%")
    print(f"   Fehler:                   {kpis['errors']}")

    print(f"\n⏱️  DURCHGANGSZEITEN")
    cs = kpis["cycle_stats"]
    print(f"   Ø pro Durchgang:          {cs['avg']:.2f} s")
    print(f"   Min / Max:                {cs['min']:.2f} s / {cs['max']:.2f} s")
    print(f"   Standardabweichung:       {cs['std']:.2f} s")

    print(f"\n🔧 PHASENZEITEN")
    for phase, stats in kpis["phase_stats"].items():
        if stats["count"] > 0:
            print(f"   {phase:20s}  Ø {stats['avg']:6.2f} s  "
                  f"(min {stats['min']:.2f}, max {stats['max']:.2f}, "
                  f"σ {stats['std']:.2f})")

    print(f"\n🎨 FARBVERTEILUNG")
    for color, count in sorted(kpis["color_distribution"].items(),
                               key=lambda x: -x[1]):
        pct = count / kpis["total_cycles"] * 100 if kpis["total_cycles"] else 0
        print(f"   {color:15s}  {count:3d}  ({pct:5.1f}%)")

    print("\n" + "=" * 60)


def plot_cycle_durations(kpis, outdir):
    """Liniendiagramm der Durchgangszeiten."""
    cycles = kpis["cycles"]
    durations = [c.get("total_duration", 0) for c in cycles if c.get("total_duration")]

    if not durations:
        return

    plt.figure(figsize=(12, 5))
    plt.plot(range(1, len(durations) + 1), durations, marker="o", linewidth=1, markersize=4)
    plt.axhline(mean(durations), color="red", linestyle="--", label=f"Ø {mean(durations):.2f}s")
    plt.xlabel("Durchgang")
    plt.ylabel("Dauer [s]")
    plt.title("Dauer pro Durchgang (Cycle)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    path = outdir / "cycle_durations.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def plot_phase_comparison(kpis, outdir):
    """Balkendiagramm: Vergleich der Phasenzeiten."""
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
    bars = plt.bar(phases, avgs, yerr=stds, capsize=5, color=["#3498db", "#2ecc71", "#e74c3c"])
    plt.ylabel("Dauer [s]")
    plt.title("Durchschnittliche Dauer pro Phase")
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
    """Gestapeltes Balkendiagramm: Zeitaufteilung pro Durchgang."""
    cycles = kpis["cycles"]

    pickplace = [c.get("pickplace_duration", 0) or 0 for c in cycles]
    colorsensor = [c.get("colorsensor_duration", 0) or 0 for c in cycles]
    sorter = [c.get("sorter_duration", 0) or 0 for c in cycles]

    x = range(1, len(cycles) + 1)

    plt.figure(figsize=(14, 6))
    plt.bar(x, pickplace, label="Pickplace", color="#3498db")
    plt.bar(x, colorsensor, bottom=pickplace, label="Colorsensor", color="#2ecc71")
    plt.bar(x, sorter, bottom=[p + c for p, c in zip(pickplace, colorsensor)],
            label="Sorter", color="#e74c3c")

    plt.xlabel("Durchgang")
    plt.ylabel("Dauer [s]")
    plt.title("Zeitaufteilung pro Durchgang")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    path = outdir / "phase_breakdown.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def plot_color_distribution(kpis, outdir):
    """Kreisdiagramm: Farbverteilung."""
    colors = kpis["color_distribution"]
    if not colors:
        return

    labels = list(colors.keys())
    values = list(colors.values())

    color_map = {
        "blue": "#3498db",
        "red": "#e74c3c",
        "green": "#2ecc71",
        "yellow": "#f1c40f",
        "other": "#95a5a6",
    }
    pie_colors = [color_map.get(l, "#bdc3c7") for l in labels]

    plt.figure(figsize=(8, 8))
    plt.pie(values, labels=labels, autopct="%1.1f%%", colors=pie_colors,
            startangle=90, explode=[0.02] * len(labels))
    plt.title("Erkannte Farben")

    path = outdir / "color_distribution.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def plot_action_boxplot(kpis, outdir):
    """Boxplot aller Aktionen."""
    intervals = kpis["intervals"]
    by_action = defaultdict(list)

    for iv in intervals:
        by_action[iv["action"]].append(iv["duration"])

    # Sortieren nach Durchschnitt
    sorted_actions = sorted(by_action.keys(), key=lambda a: mean(by_action[a]), reverse=True)
    values = [by_action[a] for a in sorted_actions]

    plt.figure(figsize=(14, 8))
    plt.boxplot(values, vert=False, tick_labels=sorted_actions)
    plt.xlabel("Dauer [s]")
    plt.title("Verteilung der Aktionsdauern")
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()

    path = outdir / "action_boxplot.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   → {path}")


def export_csv(kpis, outdir):
    """Exportiert Cycles und Intervalle als CSV."""
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
    parser = argparse.ArgumentParser(description="KPI-Report für Dobot-Logs")
    parser.add_argument("logfile", help="Pfad zur JSONL-Logdatei")
    parser.add_argument("--output-dir", "-o", default="report",
                        help="Ausgabeverzeichnis (default: report)")

    args = parser.parse_args()
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\n📂 Lade Log: {args.logfile}")
    events = load_events(args.logfile)
    print(f"   {len(events)} Events geladen")

    print(f"\n🔍 Analysiere Durchgänge...")
    cycles = extract_cycles(events)
    intervals = extract_action_intervals(events)
    print(f"   {len(cycles)} Durchgänge erkannt")
    print(f"   {len(intervals)} Aktionsintervalle")

    kpis = compute_kpis(cycles, intervals)
    print_report(kpis)

    print(f"\n📊 Erstelle Visualisierungen...")
    plot_cycle_durations(kpis, outdir)
    plot_phase_comparison(kpis, outdir)
    plot_phase_breakdown(kpis, outdir)
    plot_color_distribution(kpis, outdir)
    plot_action_boxplot(kpis, outdir)

    print(f"\n💾 Exportiere CSV...")
    export_csv(kpis, outdir)

    print(f"\n✅ Report erstellt in: {outdir.absolute()}\n")


if __name__ == "__main__":
    main()
