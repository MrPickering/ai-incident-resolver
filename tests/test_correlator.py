import json
from unittest.mock import MagicMock

from src.correlator import correlate_alerts, _parse_json_response


SAMPLE_ALERTS = [
    {"id": "ALT-001", "severity": "critical", "source": "prometheus", "host": "prod-web-03",
     "timestamp": "2024-01-15T03:22:00Z", "message": "Filesystem nearly full"},
    {"id": "ALT-002", "severity": "warning", "source": "prometheus", "host": "prod-web-03",
     "timestamp": "2024-01-15T03:22:15Z", "message": "Disk I/O saturation"},
]

MOCK_CORRELATION = {
    "clusters": [
        {
            "id": "INC-001",
            "root_alert": "ALT-001",
            "related_alerts": ["ALT-002"],
            "cascade_chain": "ALT-001 -> ALT-002",
            "confidence": "high",
            "summary": "Disk space exhaustion causing I/O saturation",
        }
    ],
    "noise_alerts": [],
}


def _make_mock_client(response_text):
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]
    mock_response.usage = MagicMock(input_tokens=500, output_tokens=300)
    client.messages.create.return_value = mock_response
    return client


def test_correlate_alerts_returns_clusters():
    client = _make_mock_client(json.dumps(MOCK_CORRELATION))
    result, usage = correlate_alerts(SAMPLE_ALERTS, client=client)

    assert "clusters" in result
    assert len(result["clusters"]) == 1
    assert result["clusters"][0]["root_alert"] == "ALT-001"
    assert result["clusters"][0]["confidence"] == "high"
    assert usage.input_tokens == 500
    assert usage.output_tokens == 300


def test_correlate_alerts_calls_api_correctly():
    client = _make_mock_client(json.dumps(MOCK_CORRELATION))
    correlate_alerts(SAMPLE_ALERTS, client=client)

    client.messages.create.assert_called_once()
    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-20250514"
    assert "correlat" in call_kwargs["system"].lower() or "SRE" in call_kwargs["system"]
    assert "ALT-001" in call_kwargs["messages"][0]["content"]


def test_correlate_alerts_noise_alerts():
    response = {
        "clusters": [],
        "noise_alerts": ["ALT-099"],
    }
    client = _make_mock_client(json.dumps(response))
    result, _ = correlate_alerts(SAMPLE_ALERTS, client=client)

    assert result["noise_alerts"] == ["ALT-099"]
    assert result["clusters"] == []


def test_parse_json_response_plain():
    text = '{"key": "value"}'
    assert _parse_json_response(text) == {"key": "value"}


def test_parse_json_response_with_fences():
    text = '```json\n{"key": "value"}\n```'
    assert _parse_json_response(text) == {"key": "value"}


def test_parse_json_response_with_bare_fences():
    text = '```\n{"key": "value"}\n```'
    assert _parse_json_response(text) == {"key": "value"}
