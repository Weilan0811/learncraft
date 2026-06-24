from pathlib import Path


PROMPT_ROOT = Path(__file__).resolve().parents[2] / "prompts"


def load_prompt_template(group: str, filename: str) -> str:
    return (PROMPT_ROOT / group / filename).read_text(encoding="utf-8")
