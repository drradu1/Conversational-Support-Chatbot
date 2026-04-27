import random

def experimental_style_assignment(user_message, classifier_style):
    """
    Hybrid approach (Option C):
    - Use classifier for obvious cases
    - Randomize for ambiguous/emotional cases
    - Allow variation even in emotional contexts
    """

    ALL_STYLES = ["emotional", "informational", "instrumental", "appraisal"]

    msg = user_message.lower()

    # 1. Obvious informational cases
    if any(x in msg for x in ["what is", "who is", "why", "how do i", "explain", "capital of"]):
        return "informational"

    # 2. Obvious instrumental cases
    if any(x in msg for x in ["step by step", "plan", "how to", "guide me", "instructions"]):
        return "instrumental"

    # 3. Obvious appraisal cases
    if any(x in msg for x in ["i helped", "i did well", "i succeeded", "i stopped a fight"]):
        return "appraisal"

    # 4. Crisis or high distress → emotional, but allow variation 30% of the time
    if classifier_style == "emotional":
        if random.random() < 0.3:
            return random.choice(["informational", "instrumental", "appraisal"])
        return "emotional"

    # 5. Ambiguous → randomize across all 4 styles
    return random.choice(ALL_STYLES)