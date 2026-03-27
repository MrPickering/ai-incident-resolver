#!/usr/bin/env python3
"""AI Incident Resolver - Replace 2+ hours of incident response in under 30 seconds."""

import json
import os
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.analyzer import analyze_logs
from src.benchmark import BenchmarkTracker
from src.correlator import correlate_alerts
from src.reporter import generate_report
from src.runbook import generate_runbook

console = Console()


def load_scenario(scenario_dir):
    """Load alerts and logs from a scenario directory."""
    alerts_path = os.path.join(scenario_dir, "alerts.json")
    logs_path = os.path.join(scenario_dir, "logs.txt")

    if not os.path.exists(alerts_path):
        raise click.ClickException(f"alerts.json not found in {scenario_dir}")
    if not os.path.exists(logs_path):
        raise click.ClickException(f"logs.txt not found in {scenario_dir}")

    with open(alerts_path) as f:
        alerts = json.load(f)
    with open(logs_path) as f:
        logs = f.read()

    return alerts, logs


def write_output(output_dir, correlation, analysis, runbook, report, benchmark_data):
    """Write all results to the output directory."""
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "correlation.json"), "w") as f:
        json.dump(correlation, f, indent=2)

    with open(os.path.join(output_dir, "root-cause.json"), "w") as f:
        json.dump(analysis, f, indent=2)

    with open(os.path.join(output_dir, "runbook.md"), "w") as f:
        f.write(runbook)

    with open(os.path.join(output_dir, "incident-report.md"), "w") as f:
        f.write(report)

    if benchmark_data:
        with open(os.path.join(output_dir, "benchmark.json"), "w") as f:
            json.dump(benchmark_data, f, indent=2)


def print_benchmark(benchmark_data):
    """Display benchmark results as a rich table."""
    table = Table(title="Pipeline Benchmark")
    table.add_column("Stage", style="cyan")
    table.add_column("Time (s)", justify="right", style="green")
    table.add_column("Input Tokens", justify="right")
    table.add_column("Output Tokens", justify="right")
    table.add_column("Cost (USD)", justify="right", style="yellow")

    for stage in benchmark_data["stages"]:
        table.add_row(
            stage["stage"],
            str(stage["time_seconds"]),
            f"{stage['input_tokens']:,}",
            f"{stage['output_tokens']:,}",
            f"${stage['cost_usd']:.4f}",
        )

    table.add_section()
    table.add_row(
        "TOTAL",
        str(benchmark_data["total_time_seconds"]),
        f"{benchmark_data['total_input_tokens']:,}",
        f"{benchmark_data['total_output_tokens']:,}",
        f"${benchmark_data['total_cost_usd']:.4f}",
        style="bold",
    )

    console.print(table)

    comp = benchmark_data["comparison"]
    console.print(
        f"\n[bold green]{comp['speedup_factor']}x faster[/] than manual incident response "
        f"({comp['ai_time_seconds']}s vs {comp['manual_time_minutes']} minutes)"
    )


@click.command()
@click.option(
    "--scenario",
    type=click.Path(exists=True),
    help="Path to scenario directory (contains alerts.json + logs.txt)",
)
@click.option("--alerts", "alerts_file", type=click.Path(exists=True), help="Path to alerts JSON file")
@click.option("--logs", "logs_file", type=click.Path(exists=True), help="Path to log file")
@click.option("--output", "output_dir", default="./output", help="Output directory (default: ./output)")
@click.option("--benchmark", "show_benchmark", is_flag=True, help="Show token + timing breakdown")
def cli(scenario, alerts_file, logs_file, output_dir, show_benchmark):
    """AI Incident Resolver - Analyze alerts and logs to resolve incidents fast."""
    # Load input data
    if scenario:
        alerts, logs = load_scenario(scenario)
    elif alerts_file and logs_file:
        with open(alerts_file) as f:
            alerts = json.load(f)
        with open(logs_file) as f:
            logs = f.read()
    else:
        raise click.ClickException(
            "Provide either --scenario <dir> or both --alerts <file> and --logs <file>"
        )

    console.print(Panel("[bold]AI Incident Resolver[/bold]\nAnalyzing incident...", style="blue"))

    tracker = BenchmarkTracker()
    tracker.start()

    # Stage 1: Correlate alerts
    console.print("\n[cyan]Stage 1:[/] Correlating alerts...")
    correlation = tracker.track("Alert Correlation", correlate_alerts, alerts)

    # Stage 2: Analyze logs
    console.print("[cyan]Stage 2:[/] Analyzing logs for root cause...")
    analysis = tracker.track("Log Analysis", analyze_logs, logs, correlation)

    # Stage 3: Generate runbook
    console.print("[cyan]Stage 3:[/] Generating resolution runbook...")
    runbook = tracker.track("Runbook Generation", generate_runbook, analysis, correlation)

    # Stage 4: Generate incident report
    console.print("[cyan]Stage 4:[/] Generating incident report...")
    report = tracker.track("Incident Report", generate_report, correlation, analysis, runbook)

    tracker.stop()
    benchmark_data = tracker.summary()

    # Write output
    write_output(output_dir, correlation, analysis, runbook, report, benchmark_data)
    console.print(f"\n[green]Results written to {output_dir}/[/]")

    # Display summary
    console.print(Panel(f"[bold]Root Cause:[/] {analysis.get('root_cause', 'Unknown')}", style="red"))

    if show_benchmark:
        print_benchmark(benchmark_data)

    console.print("\n[green]Done![/]")


if __name__ == "__main__":
    cli()
