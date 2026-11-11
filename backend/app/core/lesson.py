def normalize_lesson_id(lesson_id: str) -> str:
    if lesson_id.startswith("partial_lesson_"):
        return lesson_id.removeprefix("partial_")
    return lesson_id
