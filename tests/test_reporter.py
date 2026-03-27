import json
from unittest.mock import MagicMock

from src.reporter import generate_report


SAMPLE_CORRELATION = {
    "clusters": [{"id": "INC-001", "root_alert": "ALT-001", "summary": "Disk full"}],
    "noise_alerts": [],
}

SAMPLE_ANALYSIS = {
    "root_cause": "Debug logging filled /var/log",
    "timeline": [{"time": "2024-01-14T18:00:00Z", "event": "Deployment"}],
    "evidence": ["Disk usage linear growth"],
    "confidence": "high",
    "contributing_factors": ["No log rotation"],
}

SAMPLE_RUNBOOK = "# Runbook: Disk Full\n\n## 1. Immediate Mitigation\n..."

MOCK_REPORT = """# Incident Report: Disk Space Exhaustion - prod-web-03

**Incident ID:** INC-001
**Date:** 2024-01-15
**Severity:** Critical
**Duration:** 2 hours 3 minutes
**Status:** Resolved

## Executive Summary

A deployment on January 14 left debug logging enabled on prod-web-03, causing /var/log to fill at ~50GB/hr. This resulted in cascading service failures affecting the checkout API for approximately 2 hours.

## Impact

- **Duration:** 03:22 UTC to 05:25 UTC (2 hours 3 minutes)
- **Affected Services:** checkout-api, log ingestion pipeline
- **User Impact:** ~2,400 failed checkout attempts, estimated $18,000 in lost revenue

## Timeline

| Time (UTC) | Event |
|---|---|
| Jan 14 18:00 | Deployment of checkout-api v2.14.3 with debug logging |
| Jan 15 03:22 | First disk space alert (2% remaining) |
| Jan 15 03:24 | Checkout API returning 500 errors |
| Jan 15 05:25 | Service restored after manual intervention |

## Root Cause

Debug logging (LOG_LEVEL=DEBUG, SQL_QUERY_LOGGING=true) was enabled in the deployment configuration. The verbose SQL query logging generated approximately 50GB/hour of log data, exhausting the 500GB /var/log partition in approximately 9 hours.

## Resolution

1. Cleared disk space by removing old log files
2. Disabled debug logging in application configuration
3. Restarted checkout-api service
4. Verified service health and normal operation

## Action Items

| Action | Owner | Due Date |
|---|---|---|
| Add log level validation to deployment pipeline | Platform Team | 2024-01-22 |
| Configure log rotation with 10GB size limit | SRE Team | 2024-01-19 |
| Add disk usage alerting at 70% threshold | SRE Team | 2024-01-19 |
| Add deployment checklist for log level verification | Dev Team | 2024-01-26 |

## Lessons Learned

1. Debug logging should never be enabled in production without explicit time-boxed approval
2. Log rotation must have size-based limits, not just time-based rotation
3. Disk usage alerts should trigger well before critical thresholds
"""


def _make_mock_client(response_text):
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]
    mock_response.usage = MagicMock(input_tokens=1500, output_tokens=1200)
    client.messages.create.return_value = mock_response
    return client


def test_generate_report_returns_markdown():
    client = _make_mock_client(MOCK_REPORT)
    result, usage = generate_report(SAMPLE_CORRELATION, SAMPLE_ANALYSIS, SAMPLE_RUNBOOK, client=client)

    assert isinstance(result, str)
    assert "# Incident Report" in result
    assert usage.input_tokens == 1500


def test_generate_report_has_all_sections():
    client = _make_mock_client(MOCK_REPORT)
    result, _ = generate_report(SAMPLE_CORRELATION, SAMPLE_ANALYSIS, SAMPLE_RUNBOOK, client=client)

    assert "Executive Summary" in result
    assert "Impact" in result
    assert "Timeline" in result
    assert "Root Cause" in result
    assert "Resolution" in result
    assert "Action Items" in result
    assert "Lessons Learned" in result


def test_generate_report_calls_api_with_all_inputs():
    client = _make_mock_client(MOCK_REPORT)
    generate_report(SAMPLE_CORRELATION, SAMPLE_ANALYSIS, SAMPLE_RUNBOOK, client=client)

    call_kwargs = client.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    assert "INC-001" in user_content
    assert "root_cause" in user_content
    assert "Runbook" in user_content


def test_generate_report_uses_correct_model():
    client = _make_mock_client(MOCK_REPORT)
    generate_report(SAMPLE_CORRELATION, SAMPLE_ANALYSIS, SAMPLE_RUNBOOK, client=client)

    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-20250514"
