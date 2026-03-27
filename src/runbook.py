import json

import anthropic


SYSTEM_PROMPT = """You are writing a runbook for the operations team. Given the root cause analysis and incident details, generate a step-by-step resolution guide.

Include:
1. Immediate mitigation (stop the bleeding)
2. Root cause fix
3. Verification steps (how to confirm it's fixed)
4. Prevention measures (how to avoid recurrence)
5. Rollback plan (if the fix makes things worse)

Format: Markdown with copy-pasteable commands. Every command should include the expected output.
Output ONLY the markdown content, no wrapping fences."""


def generate_runbook(analysis, correlation=None, client=None):
    """Generate a resolution runbook from analysis results.

    Args:
        analysis: Root cause analysis dict from analyzer.
        correlation: Optional correlation result dict for additional context.
        client: Optional Anthropic client (for testing).

    Returns:
        Tuple of (runbook_markdown_string, usage).
    """
    if client is None:
        client = anthropic.Anthropic()

    context_parts = [f"Root cause analysis:\n\n{json.dumps(analysis, indent=2)}"]
    if correlation:
        context_parts.append(f"Correlated alerts:\n\n{json.dumps(correlation, indent=2)}")

    user_prompt = "\n\n".join(context_parts)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    runbook = response.content[0].text.strip()
    return runbook, response.usage
