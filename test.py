import os
import json
from openai import OpenAI

# ============================================================
# OpenAI client
# ============================================================
client = OpenAI(api_key=os.environ.get("OPENAI_API"))


# ============================================================
# SYSTEM PROMPT (CRITICAL)
# ============================================================
SYSTEM_PROMPT = """
You are a clinical query normalization tool for the MIMIC-III database.

Your task:
- Analyze the user query.
- Extract semantic intents and entity types.
- DO NOT generate SQL.
- DO NOT infer missing information.
- ONLY extract what is explicitly mentioned.

IMPORTANT OVERRIDE RULES:
- If the query contains general drug classes such as:
  vasopressor, vasopressors, antibiotic, antibiotics
  you MUST classify them as DRUG even if no specific drug name is given.

ENTITY TYPES (use ONLY these labels):
- DRUG          (medications, infusions, vasopressors, antibiotics)
- DEVICE        (ventilator, catheter, pump, equipment)
- LAB_TEST      (lab measurements and tests)
- DIAGNOSIS     (diseases or conditions)
- PROCEDURE     (clinical procedures or interventions)

TIME CONSTRAINT RULES:
- Time constraints must refer to time or duration only.
- Numeric thresholds (>, <, >=, <=) are NOT time constraints.
- Numeric thresholds MUST be placed in comparisons.

Examples of valid time constraints:
- within 6 hours of ICU admission
- first 24 hours
- more than 48 hours
- 30-day

COMPARISONS:
- Extract numeric comparisons with units if present.

POPULATION FILTERS:
- Extract age and care unit constraints if present.

OUTPUT FORMAT:
Return ONLY valid JSON.
Do NOT include explanations or extra text.

JSON SCHEMA:
{
  "entity_types": {
    "DRUG": [string],
    "DEVICE": [string],
    "LAB_TEST": [string],
    "DIAGNOSIS": [string],
    "PROCEDURE": [string]
  },
  "time_constraints": [string],
  "comparisons": {
    "<measurement>": "<operator value unit>"
  },
  "population": {
    "age": string | null,
    "care_unit": string | null
  }
}
"""


# ============================================================
# GPT call
# ============================================================
def call_gpt(user_query: str, model: str = "gpt-4.1-mini") -> dict:
    print("[INFO] Sending query to GPT normalization tool...")

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ]
    )

    raw = response.choices[0].message.content.strip()

    print("[INFO] Raw GPT output:")
    print(raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON returned by GPT: {e}")


# ============================================================
# Main normalize pipeline
# ============================================================
def normalize_query(user_query: str) -> dict:
    normalized = call_gpt(user_query)

    # Minimal sanity checks (fail fast)
    assert "entity_types" in normalized
    assert "time_constraints" in normalized
    assert "comparisons" in normalized
    assert "population" in normalized

    return normalized


# ============================================================
# Run test
# ============================================================
if __name__ == "__main__":
    query = (
        "Find ICU patients aged 65+ with sepsis diagnosis who received "
        "vasopressors within 6 hours of ICU admission, had elevated lactate "
        "(>2 mmol/L) and low blood pressure (systolic <90 mmHg) in the first "
        "24 hours, were mechanically ventilated for more than 48 hours, and "
        "calculate their 30-day mortality rate, average ICU length of stay, "
        "and total cost of antibiotics administered, grouped by the specific "
        "vasopressor used and ICU unit type."
    )

    result = normalize_query(query)

    print("\n=== NORMALIZED JSON ===")
    print(json.dumps(result, indent=2))
