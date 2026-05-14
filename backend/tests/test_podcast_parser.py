from app.generators.podcast_generator import ensure_opening_phrase, normalize_dialogue, parse_dialogue_segments


def test_podcast_parser_accepts_html_escaped_person_tags() -> None:
    raw = (
        "&lt;Person1&gt;欢迎来到 未来学习电台 —— 把复杂问题讲清楚。今天聊 Agent。&lt;/Person1&gt;\n"
        "&lt;Person2&gt;我很期待这个话题。&lt;/Person2&gt;"
    )

    normalized = normalize_dialogue(raw)
    segments = parse_dialogue_segments(normalized)

    assert normalized.startswith("<Person1>")
    assert segments[0].speaker == "Person1"
    assert segments[0].voice == "Ethan"
    assert segments[1].speaker == "Person2"
    assert segments[1].voice == "Cherry"


def test_podcast_parser_accepts_plain_speaker_lines() -> None:
    raw = "\n".join(
        [
            "Person1: 欢迎来到 未来学习电台 —— 把复杂问题讲清楚。今天聊 Agent。",
            "Person2：我很期待这个话题。",
            "Person1: 这里的关键是先生成完整脚本。",
        ]
    )

    normalized = normalize_dialogue(raw)
    segments = parse_dialogue_segments(normalized)

    assert normalized.count("<Person1>") == 2
    assert normalized.count("<Person2>") == 1
    assert [segment.speaker for segment in segments] == ["Person1", "Person2", "Person1"]


def test_ensure_opening_phrase_canonicalizes_first_person1_turn() -> None:
    raw = "\n".join(
        [
            "<Person1>欢迎来到未来学习电台，把复杂问题讲清楚。今天聊 AI Agent。</Person1>",
            "<Person2>我很期待这个话题。</Person2>",
        ]
    )

    normalized = ensure_opening_phrase(raw, podcast_name="未来学习电台", podcast_tagline="把复杂问题讲清楚")

    assert normalized.startswith("<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。今天聊 AI Agent。")
