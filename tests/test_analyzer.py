import json
from unittest.mock import MagicMock

from src.analyzer import analyze_logs


SAMPLE_LOGS = """Jan 15 03:22:00 prod-web-03 prometheus[1501]: ALERT FIRING: filesystem nearly full
Jan 15 03:23:00 prod-web-03 checkout-api[5102]: ERROR Failed to write to log file"""

SAMPLE_CORRELATION = {
    "clusters": [
        {
            "id": "INC-001",
            "root_alert": "ALT-001",
            "related_alerts": ["ALT-002"],
            "cascade_chain": "ALT-001 -> ALT-002",
            "confidence": "high",
            "summary": "Disk space exhaustion",
        }
    ],
    "noise_alerts": [],
}

MOCK_ANALYSIS = {
    "root_cause": "Debug logging left enabled after deployment filled /var/log",
    "timeline": [
        {"time": "2024-01-14T18:00:00Z", "event": "Deployment with debug logging enabled"},
        {"time": "2024-01-15T03:22:00Z", "event": "Disk reached 98% capacity"},
    ],
    "evidence": [
        "Log entry shows DEBUG level enabled at 18:00",
        "Disk usage shows linear growth from deployment time",
    ],
    "confidence": "high",
    "contributing_factors": [
        "No log rotation configured for debug logs",
        "No disk usage alerting below 90%",
    ],
}


def _make_mock_client(response_text):
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]
    mock_response.usage = MagicMock(input_tokens=1200, output_tokens=600)
    client.messages.create.return_value = mock_response
    return client


def test_analyze_logs_returns_root_cause():
    client = _make_mock_client(json.dumps(MOCK_ANALYSIS))
    result, usage = analyze_logs(SAMPLE_LOGS, SAMPLE_CORRELATION, client=client)

    assert "root_cause" in result
    assert "timeline" in result
    assert "evidence" in result
    assert "confidence" in result
    assert len(result["timeline"]) == 2
    assert usage.input_tokens == 1200


def test_analyze_logs_calls_api_with_both_inputs():
    client = _make_mock_client(json.dumps(MOCK_ANALYSIS))
    analyze_logs(SAMPLE_LOGS, SAMPLE_CORRELATION, client=client)

    call_kwargs = client.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    # Should contain both correlation data and logs
    assert "INC-001" in user_content
    assert "prometheus" in user_content


def test_analyze_logs_includes_contributing_factors():
    client = _make_mock_client(json.dumps(MOCK_ANALYSIS))
    result, _ = analyze_logs(SAMPLE_LOGS, SAMPLE_CORRELATION, client=client)

    assert "contributing_factors" in result
    assert len(result["contributing_factors"]) >= 1


def test_analyze_logs_handles_fenced_json():
    fenced = f"```json\n{json.dumps(MOCK_ANALYSIS)}\n```"
    client = _make_mock_client(fenced)
    result, _ = analyze_logs(SAMPLE_LOGS, SAMPLE_CORRELATION, client=client)

    assert result["root_cause"] == MOCK_ANALYSIS["root_cause"]
