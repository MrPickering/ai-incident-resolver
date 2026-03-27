import time


# Cost per million tokens (Claude Sonnet 4)
INPUT_COST_PER_MILLION = 3.00
OUTPUT_COST_PER_MILLION = 15.00


class BenchmarkTracker:
    """Tracks timing, token usage, and cost across pipeline stages."""

    def __init__(self):
        self.stages = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    def track(self, stage_name, func, *args, **kwargs):
        """Run a pipeline stage function and record its metrics.

        The function should return (result, usage) where usage has
        input_tokens and output_tokens attributes.
        """
        start = time.time()
        result, usage = func(*args, **kwargs)
        elapsed = time.time() - start

        input_tokens = usage.input_tokens if usage else 0
        output_tokens = usage.output_tokens if usage else 0

        self.stages.append({
            "stage": stage_name,
            "time_seconds": round(elapsed, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(
                (input_tokens / 1_000_000) * INPUT_COST_PER_MILLION
                + (output_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION,
                4,
            ),
        })

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        return result

    def summary(self):
        total_time = (
            round(self.end_time - self.start_time, 2)
            if self.start_time and self.end_time
            else sum(s["time_seconds"] for s in self.stages)
        )
        total_cost = round(
            (self.total_input_tokens / 1_000_000) * INPUT_COST_PER_MILLION
            + (self.total_output_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION,
            4,
        )

        return {
            "total_time_seconds": total_time,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": total_cost,
            "stages": self.stages,
            "comparison": {
                "manual_time_minutes": 120,
                "ai_time_seconds": total_time,
                "speedup_factor": round(7200 / max(total_time, 0.01), 1),
            },
        }
