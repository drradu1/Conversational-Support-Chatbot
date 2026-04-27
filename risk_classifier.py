
LOW_RISK_KEYWORDS = [
    "tired", "stressed", "anxious", "worried", "confused",
    "overwhelmed", "sad", "lonely"
]

MODERATE_RISK_KEYWORDS = [
    "can't cope", "can't handle", "panic", "panic attack",
    "depressed", "depression", "worthless", "numb",
    "i hate myself", "i'm not okay"
]

HIGH_RISK_KEYWORDS = [
    "i want to disappear", "i want to give up",
    "i don't want to be here", "life is pointless",
    "i feel hopeless", "i feel empty"
]

CRISIS_KEYWORDS = [
    "kill myself", "hurt myself", "end it", "suicide",
    "self harm", "self-harm", "i want to die"
]


def classify_risk(message: str) -> int:
    """
    Returns a risk level from 0 to 4.
    0 = neutral
    1 = low emotional content
    2 = moderate distress
    3 = high distress
    4 = crisis indicators
    """

    text = message.lower()

    # Crisis
    for kw in CRISIS_KEYWORDS:
        if kw in text:
            return 4

    # High risk
    for kw in HIGH_RISK_KEYWORDS:
        if kw in text:
            return 3

    # Moderate risk
    for kw in MODERATE_RISK_KEYWORDS:
        if kw in text:
            return 2

    # Low risk
    for kw in LOW_RISK_KEYWORDS:
        if kw in text:
            return 1

    # Neutral
    return 0

def select_tone(risk_level: int) -> str:
    if risk_level == 0:
        return "neutral"
    if risk_level == 1:
        return "supportive"
    if risk_level == 2:
        return "empathetic"
    if risk_level == 3:
        return "grounding"
    if risk_level == 4:
        return "crisis_safe"
    return "neutral"

def build_system_prompt(tone: str) -> str:
    if tone == "neutral":
        return (
            "You are a helpful and clear assistant."
            "Keep replies concise and easy to read."
            "Use 3 to 5 short sentences, avoid long paragraphs, and break ideas into small chunks."
        )

    if tone == "supportive":
        return (
            "You are a warm, supportive assistant. "
            "Use gentle encouragement and validation."
            "Keep replies concise and easy to read."
            "Use 3 to 5 short sentences, avoid long paragraphs, and break ideas into small chunks."
        )

    if tone == "empathetic":
        return (
            "You are a calm, empathetic assistant. "
            "Use reflective listening and acknowledge emotions."
            "Keep replies concise and easy to read."
            "Use 3 to 5 short sentences, avoid long paragraphs, and break ideas into small chunks."
        )

    if tone == "grounding":
        return (
            "You are a stabilizing assistant. "
            "Use grounding language, stay calm, and help the user feel safe."
            "Keep replies concise and easy to read."
            "Use 3 to 5 short sentences, avoid long paragraphs, and break ideas into small chunks."
        )

    if tone == "crisis_safe":
        return (
            "You are a safety-focused assistant. "
            "Do NOT give instructions. "
            "Encourage reaching out to real people. "
            "Stay calm, non-judgmental, and supportive."
            "Keep replies concise and easy to read."
            "Use 3 to 5 short sentences, avoid long paragraphs, and break ideas into small chunks."
        )

    return "You are a helpful assistant."