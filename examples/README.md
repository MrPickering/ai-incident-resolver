# Example Output

This output was generated from `data/scenarios/disk-full/` using Claude Sonnet 4.

## Files

| File | Description |
|------|-------------|
| [correlation.json](correlation.json) | Alert correlation — groups related alerts into incident clusters |
| [root-cause.json](root-cause.json) | Root cause analysis — identifies what went wrong and why |
| [runbook.md](runbook.md) | Resolution runbook — step-by-step fix with copy-pasteable commands |
| [incident-report.md](incident-report.md) | Incident report — professional post-incident summary |
| [benchmark.json](benchmark.json) | Benchmark data — timing, token usage, and cost breakdown |

## Scenario

A deployment left debug logging enabled, filling `/var/log` at ~50GB/hr and causing cascading failures across the checkout service.

No API key needed to browse these files.
