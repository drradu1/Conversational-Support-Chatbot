def classify_message_type(message: str) -> str:
    msg = message.lower()

    # Emotional self-disclosure
    if any(x in msg for x in [
        "i feel", "i am not", "i'm not", "i can't", "i don't know",
        "i'm scared", "i'm sad", "i'm anxious", "i'm stressed",
        "i feel like", "i'm worried"
    ]):
        return "emotional"

    # Task / request for help
    if any(x in msg for x in [
        "how do i", "how to", "can you help", "step by step",
        "guide me", "what should i do", "plan", "instructions"
    ]):
        return "task"

    # Factual question
    if any(x in msg for x in [
        "what is", "who is", "where is", "why", "explain", "capital of"
    ]):
        return "factual"

    # Gratitude / positive sentiment
    if any(x in msg for x in [
        "thank you", "thanks", "appreciate", "sounds good", "cool"
    ]):
        return "gratitude"

    # Casual / neutral
    if msg in ["hi", "hello", "hey", "ok", "yes", "no"]:
        return "casual"

    # Default
    return "other"