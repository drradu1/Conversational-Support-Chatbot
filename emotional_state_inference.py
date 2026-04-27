import json

def infer_emotional_state(client, user_message: str) -> dict:
    system_prompt = (
        "You analyze short user messages for emotional and psychological indicators.\n"
        "You MUST output ONLY valid JSON. No explanations. No text before or after.\n"
        "Return EXACTLY this structure:\n"
        "{\n"
        "  \"distress_level\": \"none|mild|moderate|high|crisis\",\n"
        "  \"emotional_indicators\": [\"...\"],\n"
        "  \"other_notes\": \"...\"\n"
        "}\n"
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.2,
        max_tokens=200
    )

    raw = response.choices[0].message.content

    try:
        return json.loads(raw)
    except Exception:
        return {
            "distress_level": "none",
            "emotional_indicators": [],
            "other_notes": "Parsing error; fallback to neutral."
        }