import time
from unittest.mock import MagicMock

from src.benchmark import BenchmarkTracker, INPUT_COST_PER_MILLION, OUTPUT_COST_PER_MILLION


def _make_usage(input_tokens, output_tokens):
    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    return usage


def test_tracker_tracks_single_stage():
    tracker = BenchmarkTracker()

    def fake_func():
        return {"result": "ok"}, _make_usage(100, 200)

    result = tracker.track("test-stage", fake_func)

    assert result == {"result": "ok"}
    assert len(tracker.stages) == 1
    assert tracker.stages[0]["stage"] == "test-stage"
    assert tracker.stages[0]["input_tokens"] == 100
    assert tracker.stages[0]["output_tokens"] == 200
    assert tracker.stages[0]["time_seconds"] >= 0


def test_tracker_accumulates_tokens():
    tracker = BenchmarkTracker()

    tracker.track("stage1", lambda: ("a", _make_usage(100, 200)))
    tracker.track("stage2", lambda: ("b", _make_usage(300, 400)))

    assert tracker.total_input_tokens == 400
    assert tracker.total_output_tokens == 600


def test_tracker_passes_args():
    tracker = BenchmarkTracker()

    def add(a, b):
        return a + b, _make_usage(10, 20)

    result = tracker.track("add", add, 3, 5)
    assert result == 8


def test_tracker_passes_kwargs():
    tracker = BenchmarkTracker()

    def greet(name="world"):
        return f"hello {name}", _make_usage(10, 20)

    result = tracker.track("greet", greet, name="claude")
    assert result == "hello claude"


def test_summary_totals():
    tracker = BenchmarkTracker()
    tracker.start()
    tracker.track("s1", lambda: ("x", _make_usage(1000, 500)))
    tracker.track("s2", lambda: ("y", _make_usage(2000, 1000)))
    tracker.stop()

    summary = tracker.summary()

    assert summary["total_input_tokens"] == 3000
    assert summary["total_output_tokens"] == 1500
    assert summary["total_time_seconds"] >= 0
    assert len(summary["stages"]) == 2

    expected_cost = (3000 / 1_000_000) * INPUT_COST_PER_MILLION + (1500 / 1_000_000) * OUTPUT_COST_PER_MILLION
    assert abs(summary["total_cost_usd"] - round(expected_cost, 4)) < 0.0001


def test_summary_comparison():
    tracker = BenchmarkTracker()
    tracker.start()
    tracker.track("s1", lambda: ("x", _make_usage(100, 100)))
    tracker.stop()

    summary = tracker.summary()

    assert "comparison" in summary
    assert summary["comparison"]["manual_time_minutes"] == 120
    assert summary["comparison"]["speedup_factor"] > 0


def test_cost_calculation():
    tracker = BenchmarkTracker()
    tracker.track("s1", lambda: ("x", _make_usage(1_000_000, 1_000_000)))

    stage = tracker.stages[0]
    expected = INPUT_COST_PER_MILLION + OUTPUT_COST_PER_MILLION
    assert abs(stage["cost_usd"] - expected) < 0.01


def test_summary_without_start_stop():
    tracker = BenchmarkTracker()
    tracker.track("s1", lambda: ("x", _make_usage(100, 100)))

    summary = tracker.summary()
    # Should use sum of stage times when start/stop not called
    assert summary["total_time_seconds"] >= 0
