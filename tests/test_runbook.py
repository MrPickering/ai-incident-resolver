import json
from unittest.mock import MagicMock

from src.runbook import generate_runbook


SAMPLE_ANALYSIS = {
    "root_cause": "Debug logging filled /var/log",
    "timeline": [
        {"time": "2024-01-14T18:00:00Z", "event": "Deployment with debug logging"},
    ],
    "evidence": ["Disk usage linear growth"],
    "confidence": "high",
    "contributing_factors": ["No log rotation"],
}

SAMPLE_CORRELATION = {
    "clusters": [{"id": "INC-001", "root_alert": "ALT-001", "summary": "Disk full"}],
    "noise_alerts": [],
}

MOCK_RUNBOOK = """# Runbook: Disk Space Exhaustion on prod-web-03

## 1. Immediate Mitigation

Clear space on the affected host:

```bash
# Check current disk usage
df -h /var/log
# Expected: /var/log at 98%+ usage

# Remove old rotated logs
sudo rm -f /var/log/checkout-api.log.[0-9]*
# Expected: Several GB freed

# Truncate the active debug log
sudo truncate -s 0 /var/log/checkout-api.log
# Expected: File size reset to 0
```

## 2. Root Cause Fix

Disable debug logging:

```bash
# Update application config
sudo sed -i 's/LOG_LEVEL=DEBUG/LOG_LEVEL=INFO/' /etc/checkout-api/config.env
# Expected: No output (successful edit)

# Restart the service
sudo systemctl restart checkout-api
# Expected: Service restarts cleanly
```

## 3. Verification Steps

```bash
# Verify disk space recovered
df -h /var/log
# Expected: /var/log below 50% usage

# Verify service is healthy
curl -s http://localhost:8080/health | jq .
# Expected: {"status": "healthy"}
```

## 4. Prevention Measures

- Configure log rotation with size limits
- Add alerting for disk usage at 70% threshold
- Add deployment checklist item to verify log levels

## 5. Rollback Plan

If issues persist after fix:
```bash
sudo systemctl stop checkout-api
sudo cp /etc/checkout-api/config.env.bak /etc/checkout-api/config.env
sudo systemctl start checkout-api
```
"""


def _make_mock_client(response_text):
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]
    mock_response.usage = MagicMock(input_tokens=800, output_tokens=900)
    client.messages.create.return_value = mock_response
    return client


def test_generate_runbook_returns_markdown():
    client = _make_mock_client(MOCK_RUNBOOK)
    result, usage = generate_runbook(SAMPLE_ANALYSIS, client=client)

    assert isinstance(result, str)
    assert "# Runbook" in result
    assert "Immediate Mitigation" in result
    assert usage.output_tokens == 900


def test_generate_runbook_contains_commands():
    client = _make_mock_client(MOCK_RUNBOOK)
    result, _ = generate_runbook(SAMPLE_ANALYSIS, client=client)

    assert "```bash" in result or "```" in result
    assert "df -h" in result


def test_generate_runbook_has_all_sections():
    client = _make_mock_client(MOCK_RUNBOOK)
    result, _ = generate_runbook(SAMPLE_ANALYSIS, client=client)

    assert "Immediate Mitigation" in result
    assert "Root Cause Fix" in result
    assert "Verification" in result
    assert "Prevention" in result
    assert "Rollback" in result


def test_generate_runbook_with_correlation():
    client = _make_mock_client(MOCK_RUNBOOK)
    generate_runbook(SAMPLE_ANALYSIS, correlation=SAMPLE_CORRELATION, client=client)

    call_kwargs = client.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    assert "INC-001" in user_content


def test_generate_runbook_without_correlation():
    client = _make_mock_client(MOCK_RUNBOOK)
    generate_runbook(SAMPLE_ANALYSIS, client=client)

    call_kwargs = client.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    assert "root_cause" in user_content
