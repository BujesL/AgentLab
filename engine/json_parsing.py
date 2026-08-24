import json
import re


def parse_json_object(raw: str) -> dict:
    """Parse a JSON object out of raw LLM output.

    Local models don't always honor `format: "json"` strictly — some wrap the
    object in prose or code fences. Falls back to extracting the first
    `{...}` block before giving up.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))
