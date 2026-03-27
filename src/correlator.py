import json

import anthropic


SYSTEM_PROMPT = """You are an SRE incident commander. Given a set of monitoring alerts, correlate them into incident clusters.

For each cluster:
1. Group related alerts (same host, same time window, causal chain)
2. Identify the likely root alert (the one that preceded others)
3. Map the cascade: which alert caused which
4. Rate confidence (high/medium/low)

You MUST respond with ONLY valid JSON in this exact format, no markdown fences:
{
  "clusters": [
    {
      "id": "INC-001",
      "root_alert": "<alert_id>",
      "related_alerts": ["<alert_id>", ...],
      "cascade_chain": "<alert_id> -> <alert_id> -> ...",
      "confidence": "high|medium|low",
      "summary": "<brief description>"
    }
  ],
  "noise_alerts": []
}"""


def _parse_json_response(text):
    """Parse JSON from Claude's response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def correlate_alerts(alerts, client=None):
    """Correlate monitoring alerts into incident clusters.

    Args:
        alerts: List of alert dictionaries.
        client: Optional Anthropic client (for testing).

    Returns:
        Tuple of (correlation_result_dict, usage).
    """
    if client is None:
        client = anthropic.Anthropic()

    user_prompt = f"Analyze and correlate these monitoring alerts:\n\n{json.dumps(alerts, indent=2)}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    result = _parse_json_response(response.content[0].text)
    return result, response.usage
