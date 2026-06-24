from app.schemas.outline import OutlineUnit


def choose_slide_layout(unit: OutlineUnit) -> str:
    if unit.visual_strategy in ("image_text", "visual_summary"):
        return unit.visual_strategy
    if unit.visual_strategy in ("process", "timeline", "comparison", "summary"):
        return "visual_summary"
    return "image_text"


def design_intent_for_layout(layout: str) -> str:
    intents = {
        "image_text": "Pair the core explanation with a supporting teaching visual.",
        "visual_summary": "Present a structured summary diagram with concise text.",
    }
    return intents.get(layout, intents["image_text"])
