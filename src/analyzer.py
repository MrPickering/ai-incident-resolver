import json

import anthropic


SYSTEM_PROMPT = """You are a senior SRE performing root cause analysis. Given application logs and correlated alerts, identify the root cause.

Analyze:
1. Timeline of events (first error to current state)
2. Pattern changes (what started appearing that wasn't before)
3. Resource exhaustion indicators
4. Configuration or deployment changes
5. External dependency failures

You MUST respond with ONLY valid JSON in this exact format, no markdown fences:
{
  "root_cause": "<concise description of the root cause>",
  "timeline": [
    {"time": "<ISO timestamp>", "event": "<what happened>"}
  ],
  "evidence": ["<log line or observation supporting the conclusion>"],
  "confidence": "high|medium|low",
  "contributing_factors": ["<factor that made the issue worse>"]
}"""


def _parse_json_response(text):
    """Parse JSON from Claude's response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def analyze_logs(logs, correlation, client=None):
    """Perform root cause analysis on logs using correlated alert data.

    Args:
        logs: Raw log text string.
        correlation: Correlation result dict from correlator.
        client: Optional Anthropic client (for testing).

    Returns:
        Tuple of (analysis_result_dict, usage).
    """
    if client is None:
        client = anthropic.Anthropic()

    user_prompt = (
        f"Here are the correlated alerts:\n\n{json.dumps(correlation, indent=2)}\n\n"
        f"Here are the application logs:\n\n{logs}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    result = _parse_json_response(response.content[0].text)
    return result, response.usage
