'''
Streamlit dashboard for visualizing KPIs from Dobot logs.

Usage:
    streamlit run dashboard.py
'''

import io
import tempfile
import contextlib
from pathlib import Path

import streamlit as st
import pandas as pd

from generate_kpi import (
    load_events,
    extract_cycles,
    extract_action_intervals,
    compute_kpis,
    print_report,
    plot_cycle_durations,
    plot_phase_comparison,
    plot_phase_breakdown,
    plot_color_distribution,
    plot_action_boxplot,
    plot_gantt,
    plot_latencies,
)

st.set_page_config(
    page_title="Dobot KPI Dashboard",
    layout="wide",
)

st.title("Dobot KPI Dashboard")

uploaded_file = st.file_uploader("Upload JSONL Log File", type=["jsonl"])

if not uploaded_file:
    st.info("Bitte ein JSONL-Logfile hochladen.")
    st.stop()


# ---------- Daten laden & KPIs berechnen ----------
@st.cache_data(show_spinner="Analyse läuft...")
def analyze(file_bytes: bytes):
    """Schreibt Upload temporär, generiert KPIs + alle Plots in einem Temp-Ordner."""
    tmpdir = Path(tempfile.mkdtemp(prefix="dobot_kpi_"))
    log_path = tmpdir / "log.jsonl"
    log_path.write_bytes(file_bytes)

    events = load_events(str(log_path))
    cycles = extract_cycles(events)
    intervals = extract_action_intervals(events)
    kpis = compute_kpis(cycles, intervals, events)

    # Terminal-Report in String umleiten
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_report(kpis)
    report_text = buf.getvalue()

    # Alle Plots generieren (unterdrücke print-Ausgaben der Plot-Funktionen)
    plotdir = tmpdir / "plots"
    plotdir.mkdir(exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()):
        plot_cycle_durations(kpis, plotdir)
        plot_phase_comparison(kpis, plotdir)
        plot_phase_breakdown(kpis, plotdir)
        plot_color_distribution(kpis, plotdir)
        plot_action_boxplot(kpis, plotdir)
        plot_gantt(kpis, plotdir)
        plot_latencies(kpis["latencies"], plotdir)

    return events, kpis, report_text, plotdir


events, kpis, report_text, plotdir = analyze(uploaded_file.getvalue())


# ---------- KPI Cards ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cycles", kpis["total_cycles"])
col2.metric("Runtime", f"{kpis['total_runtime']:.2f} s")
col3.metric("Success Rate", f"{kpis['success_rate']:.1f}%")
col4.metric("Errors", kpis["errors"])

st.divider()


# ---------- Tabs ----------
tab_overview, tab_cycles, tab_phases, tab_colors, tab_actions, tab_latency, tab_gantt, tab_data = st.tabs(
    ["Übersicht", "Zyklen", "Phasen", "Farben", "Actions", "Latenzen", "Gantt", "Rohdaten"]
)


# --- Übersicht: Terminal-Report ---
with tab_overview:
    st.subheader("KPI Report (Terminal-Output)")
    st.code(report_text, language="text")


# --- Zyklen ---
with tab_cycles:
    st.subheader("Duration per Cycle")
    st.image(str(plotdir / "cycle_durations.png"))

    st.subheader("Cycle Stats")
    st.dataframe(pd.DataFrame([kpis["cycle_stats"]]).T.rename(columns={0: "value"}))


# --- Phasen ---
with tab_phases:
    st.subheader("Average Duration per Phase")
    st.image(str(plotdir / "phase_comparison.png"))

    st.subheader("Time Distribution per Cycle")
    st.image(str(plotdir / "phase_breakdown.png"))

    st.subheader("Phase Statistics")
    st.dataframe(pd.DataFrame(kpis["phase_stats"]).T)


# --- Farben ---
with tab_colors:
    st.subheader("Detected Colors")
    color_png = plotdir / "color_distribution.png"
    if color_png.exists():
        st.image(str(color_png))
    else:
        st.info("Keine Farbdaten verfügbar.")

    st.dataframe(
        pd.DataFrame(
            list(kpis["color_distribution"].items()),
            columns=["Color", "Count"],
        )
    )


# --- Actions ---
with tab_actions:
    st.subheader("Distribution of Action Durations")
    st.image(str(plotdir / "action_boxplot.png"))

    st.subheader("Action Statistics")
    st.dataframe(pd.DataFrame(kpis["action_stats"]).T)


# --- Latenzen ---
with tab_latency:
    st.subheader("Latency Distribution")
    lat_png = plotdir / "latencies.png"
    if lat_png.exists():
        st.image(str(lat_png))
    else:
        st.info("Keine Latenzdaten verfügbar.")

    st.subheader("Latency Statistics (ms)")
    rows = []
    for name, stats in kpis["latency_stats"].items():
        if stats:
            rows.append({
                "metric": name,
                "count": stats["count"],
                "avg_ms": stats["avg"] * 1000,
                "min_ms": stats["min"] * 1000,
                "max_ms": stats["max"] * 1000,
                "p50_ms": stats["p50"] * 1000,
                "p95_ms": stats["p95"] * 1000,
                "std_ms": stats["std"] * 1000,
            })
    if rows:
        st.dataframe(pd.DataFrame(rows).set_index("metric"))


# --- Gantt ---
with tab_gantt:
    st.subheader("Gantt Chart")
    st.image(str(plotdir / "gantt_chart.png"))


# --- Rohdaten + Downloads ---
with tab_data:
    st.subheader("Cycles")
    df_cycles = pd.DataFrame(kpis["cycles"])
    st.dataframe(df_cycles)
    st.download_button(
        "Download cycles.csv",
        df_cycles.to_csv(index=False).encode("utf-8"),
        file_name="cycles.csv",
        mime="text/csv",
    )

    st.subheader("Intervals")
    df_intervals = pd.DataFrame(kpis["intervals"])
    st.dataframe(df_intervals)
    st.download_button(
        "Download intervals.csv",
        df_intervals.to_csv(index=False).encode("utf-8"),
        file_name="intervals.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download KPI Report (txt)",
        report_text.encode("utf-8"),
        file_name="kpi_report.txt",
        mime="text/plain",
    )
