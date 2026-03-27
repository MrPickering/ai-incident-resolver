# AI Incident Resolver

Part of the [PickBits.ai](https://pickbits.ai) portfolio — AI tools that demonstrate real-world productivity gains with Claude.

**Replace 2+ hours of DevOps incident response with 30 seconds of AI-powered analysis.**

AI Incident Resolver takes monitoring alerts and application logs, then uses Claude to correlate alerts, identify root causes, generate resolution runbooks with copy-pasteable commands, and produce professional incident reports — all in a single pipeline run.

## Example Output

Browse the complete output from the **disk-full** scenario — no API key needed:

| File | Description |
|------|-------------|
| [examples/correlation.json](examples/correlation.json) | Alert correlation — groups 5 related alerts into one incident cluster with cascade chain |
| [examples/root-cause.json](examples/root-cause.json) | Root cause analysis — identifies debug logging as the cause with full evidence timeline |
| [examples/runbook.md](examples/runbook.md) | Resolution runbook — step-by-step fix with `ssh`, `truncate`, `systemctl` commands |
| [examples/incident-report.md](examples/incident-report.md) | Incident report — executive summary, impact, timeline, action items with owners |
| [examples/benchmark.json](examples/benchmark.json) | Benchmark — 28.4s total, $0.16 cost, 253x faster than manual response |

## How It Works

The tool runs a 4-stage pipeline, each powered by Claude:

1. **Alert Correlation** — Groups related monitoring alerts into incident clusters, identifies the root alert, and maps the cascade chain
2. **Log Analysis** — Reads application logs alongside correlated alerts to determine the root cause, build an evidence-backed timeline, and identify contributing factors
3. **Runbook Generation** — Produces a step-by-step resolution guide with copy-pasteable commands and expected output for each step
4. **Incident Report** — Generates a professional post-incident report with executive summary, impact assessment, action items, and lessons learned

## Quick Start

```bash
# Clone the repository
git clone https://github.com/mrpickering/ai-incident-resolver.git
cd ai-incident-resolver

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your Anthropic API key

# Run against a scenario
python src/main.py --scenario data/scenarios/disk-full --benchmark
```

### CLI Options

```
python src/main.py [options]

Options:
  --scenario <dir>   Path to scenario directory (contains alerts.json + logs.txt)
  --alerts <file>    Path to alerts JSON file
  --logs <file>      Path to log file
  --output <dir>     Output directory (default: ./output)
  --benchmark        Show token + timing breakdown
```

### Included Scenarios

| Scenario | Description |
|----------|-------------|
| `disk-full` | Debug logging fills /var/log, cascading to checkout API failure |
| `memory-leak` | Unbounded session cache causes OOM kills in payment service |
| `dns-failure` | Bad config push breaks DNS forwarders, all external APIs fail |
| `cert-expiry` | TLS certificate expires after 7 days of failed auto-renewal |
| `bad-deploy` | Rolling deploy with wrong DB credentials causes partial outage |

## Token Economics

| Metric | AI Incident Resolver | Manual Process |
|--------|---------------------|----------------|
| **Time** | ~30 seconds | 2+ hours |
| **Cost** | ~$0.16 per incident | $150+ (engineer hourly rate) |
| **Output** | 4 structured artifacts | Varies by engineer |
| **Consistency** | Reproducible every time | Depends on experience |
| **Coverage** | Correlation + RCA + Runbook + Report | Usually just RCA + Report |

## Portfolio

| Project | What It Does |
|---------|-------------|
| [ai-incident-resolver](https://github.com/mrpickering/ai-incident-resolver) | Replaces 2+ hours of incident response in 30 seconds |
| [ai-code-accelerator](https://github.com/mrpickering/ai-code-accelerator) | Accelerates code development workflows with Claude |

Interested in what AI-powered tooling could do for your team? [Get in touch](https://pickbits.ai/contact)

---

*Built by [PickBits.ai](https://pickbits.ai) — AI consulting that proves results before you sign.*
