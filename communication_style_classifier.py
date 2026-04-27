
def classify_communication_style(client, user_message: str) -> str:
    """
    Classifies the user's message into one of four supportive communication styles:
    emotional, informational, instrumental, appraisal.
    """

    system_prompt = """
You are a classifier for supportive communication styles.

Choose the SINGLE most appropriate supportive style for the user's message:

- emotional: empathy, validation, acknowledging feelings
- informational: explanations, psychoeducation, clarifying concepts
- instrumental: concrete steps, action plans, what to do next
- appraisal: encouragement, affirming strengths, reinforcing competence

Respond ONLY with one word:
emotional, informational, instrumental, or appraisal.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        max_tokens=10
    )

    raw = response.choices[0].message.content.strip().lower()

    if "informational" in raw:
        return "informational"
    if "instrumental" in raw:
        return "instrumental"
    if "appraisal" in raw:
        return "appraisal"
    return "emotional"

STYLE_GUIDELINES = {
    "emotional": "Use empathy, validation, warmth, and acknowledgment of feelings.",
    "informational": "Provide clear explanations, psychoeducation, and simple clarifications.",
    "instrumental": "Offer concrete steps, action-oriented guidance, and practical suggestions.",
    "appraisal": "Affirm strengths, encourage the user, and reinforce their competence."
}