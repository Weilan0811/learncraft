from app.schemas.specs.podcast import PodcastSegmentSpec, PodcastSpec
from app.schemas.render.podcast import PodcastAudioSegment, PodcastRenderModel
from app.validators.podcast_validator import PodcastValidator


def valid_spec() -> PodcastSpec:
    dialogue = "\n".join(
        [
            "<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。今天我们聊 direct workflow。</Person1>",
            "<Person2>我很期待这个话题。这里面最值得注意的是流程更直接。</Person2>",
            "<Person1>对，它适合单一成品内容，因为不需要拆成很多教学单元。</Person1>",
            "<Person2>我想稍微补充一点，如果内容很长，还是要小心节奏。</Person2>",
            "<Person1>这个提醒很重要。我们可以把脚本先完整生成，再分段做 TTS。</Person1>",
            "<Person2>这样既保留整体叙事，也能让音频生成更可控。</Person2>",
            "<Person1>今天的 takeaway 是：direct workflow 适合播客这种完整对话成品。我们下期再见。</Person1>",
        ]
    )
    return PodcastSpec(
        id="podcast_task_123",
        title="Direct workflow podcast",
        podcast_name="未来学习电台",
        podcast_tagline="把复杂问题讲清楚",
        raw_dialogue=dialogue,
        segments=[
            PodcastSegmentSpec(segment_id="seg-001", order=1, speaker="Person1", voice="Ethan", text="欢迎来到 未来学习电台 —— 把复杂问题讲清楚。今天我们聊 direct workflow。"),
            PodcastSegmentSpec(segment_id="seg-002", order=2, speaker="Person2", voice="Cherry", text="我很期待这个话题。这里面最值得注意的是流程更直接。"),
            PodcastSegmentSpec(segment_id="seg-003", order=3, speaker="Person1", voice="Ethan", text="对，它适合单一成品内容，因为不需要拆成很多教学单元。"),
            PodcastSegmentSpec(segment_id="seg-004", order=4, speaker="Person2", voice="Cherry", text="我想稍微补充一点，如果内容很长，还是要小心节奏。"),
            PodcastSegmentSpec(segment_id="seg-005", order=5, speaker="Person1", voice="Ethan", text="这个提醒很重要。我们可以把脚本先完整生成，再分段做 TTS。"),
            PodcastSegmentSpec(segment_id="seg-006", order=6, speaker="Person2", voice="Cherry", text="这样既保留整体叙事，也能让音频生成更可控。"),
            PodcastSegmentSpec(segment_id="seg-007", order=7, speaker="Person1", voice="Ethan", text="今天的 takeaway 是：direct workflow 适合播客这种完整对话成品。我们下期再见。"),
        ],
    )


def test_podcast_validator_accepts_valid_person_dialogue_and_voice_mapping() -> None:
    report = PodcastValidator().validate_pre_render(valid_spec())

    assert report.ok is True
    assert [issue for issue in report.issues if issue.severity == "error"] == []


def test_podcast_validator_rejects_unknown_speaker_tag() -> None:
    spec = valid_spec().model_copy(update={"raw_dialogue": "<Host>欢迎来到 未来学习电台。</Host>"})

    report = PodcastValidator().validate_pre_render(spec)

    assert report.ok is False
    assert any("Only Person1 and Person2" in issue.message for issue in report.issues)


def test_podcast_validator_rejects_forbidden_tts_tags() -> None:
    spec = valid_spec().model_copy(
        update={"raw_dialogue": "<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。<emphasis>错误标签</emphasis></Person1>"}
    )

    report = PodcastValidator().validate_pre_render(spec)

    assert report.ok is False
    assert any("Forbidden TTS tag" in issue.message for issue in report.issues)


def test_podcast_validator_requires_opening_phrase() -> None:
    spec = valid_spec().model_copy(update={"raw_dialogue": "<Person1>今天我们直接开始。</Person1><Person2>好。</Person2>"})

    report = PodcastValidator().validate_pre_render(spec)

    assert report.ok is False
    assert any("opening phrase" in issue.message for issue in report.issues)


def test_podcast_validator_accepts_compact_opening_phrase_punctuation() -> None:
    dialogue = valid_spec().raw_dialogue.replace(
        "欢迎来到 未来学习电台 —— 把复杂问题讲清楚。",
        "欢迎来到未来学习电台，把复杂问题讲清楚。",
        1,
    )
    spec = valid_spec().model_copy(update={"raw_dialogue": dialogue})

    report = PodcastValidator().validate_pre_render(spec)

    assert not any("opening phrase" in issue.message for issue in report.issues)


def test_podcast_validator_requires_final_audio_after_render() -> None:
    render_model = PodcastRenderModel(
        title="Direct workflow podcast",
        podcast_name="未来学习电台",
        podcast_tagline="把复杂问题讲清楚",
        script_text="<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。</Person1>",
        segments=[
            PodcastAudioSegment(
                segment_id="seg-001",
                order=1,
                speaker="Person1",
                voice="Ethan",
                text="欢迎来到 未来学习电台 —— 把复杂问题讲清楚。",
                audio_url="/api/assets/podcast_001/download",
                status="generated",
            )
        ],
        audio_manifest_url="/api/assets/manifest/download",
    )

    report = PodcastValidator().validate_final_render(render_model)

    assert report.ok is False
    assert any("final audio" in issue.message for issue in report.issues)
