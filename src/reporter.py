import json

import anthropic


SYSTEM_PROMPT = """You are writing a post-incident report. Given all analysis results, generate a professional incident report.

Sections:
- Executive Summary (2-3 sentences)
- Impact (duration, affected services, user impact)
- Timeline
- Root Cause
- Resolution
- Action Items (with owners and due dates)
- Lessons Learned

Format: Professional markdown. Be specific and actionable.
Output ONLY the markdown content, no wrapping fences."""


def generate_report(correlation, analysis, runbook, client=None):
    """Generate a post-incident report from all analysis results.

    Args:
        correlation: Correlation result dict from correlator.
        analysis: Root cause analysis dict from analyzer.
        runbook: Generated runbook markdown string.
        client: Optional Anthropic client (for testing).

    Returns:
        Tuple of (report_markdown_string, usage).
    """
    if client is None:
        client = anthropic.Anthropic()

    user_prompt = (
        f"Alert correlation:\n\n{json.dumps(correlation, indent=2)}\n\n"
        f"Root cause analysis:\n\n{json.dumps(analysis, indent=2)}\n\n"
        f"Resolution runbook:\n\n{runbook}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    report = response.content[0].text.strip()
    return report, response.usage
