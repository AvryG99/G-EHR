import json
import re


def safe_json_extract(text: str) -> dict:
    # ```json fenced
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))

    # first {...}
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))

    raise ValueError("No valid JSON found in model output")
