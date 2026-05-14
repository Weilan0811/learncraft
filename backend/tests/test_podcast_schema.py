from pydantic import TypeAdapter

from app.content_types.registry import get_content_type_profile
from app.schemas.render import RenderModel
from app.schemas.render.podcast import PodcastRenderModel
from app.schemas.specs import ContentSpec
from app.schemas.specs.podcast import PodcastSegmentSpec, PodcastSpec


def build_podcast_spec() -> PodcastSpec:
    return PodcastSpec(
        id="podcast_task_123",
        title="Direct workflow podcast",
        podcast_name="未来学习电台",
        podcast_tagline="把复杂问题讲清楚",
        raw_dialogue=(
            "<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。今天我们聊 direct workflow。</Person1>\n"
            "<Person2>我很期待这个话题。这里面最值得注意的是它避免了不必要的 unit loop。</Person2>"
        ),
        segments=[
            PodcastSegmentSpec(
                segment_id="seg-001",
                order=1,
                speaker="Person1",
                voice="Ethan",
                text="欢迎来到 未来学习电台 —— 把复杂问题讲清楚。今天我们聊 direct workflow。",
            ),
            PodcastSegmentSpec(
                segment_id="seg-002",
                order=2,
                speaker="Person2",
                voice="Cherry",
                text="我很期待这个话题。这里面最值得注意的是它避免了不必要的 unit loop。",
            ),
        ],
    )


def test_podcast_spec_enters_content_spec_union() -> None:
    spec = build_podcast_spec()

    parsed = TypeAdapter(ContentSpec).validate_python(spec.model_dump(mode="json"))

    assert isinstance(parsed, PodcastSpec)
    assert parsed.content_type == "podcast_script"
    assert parsed.segments[0].voice == "Ethan"
    assert parsed.segments[1].voice == "Cherry"


def test_podcast_render_model_enters_render_union() -> None:
    render_model = PodcastRenderModel(
        title="Direct workflow podcast",
        podcast_name="未来学习电台",
        podcast_tagline="把复杂问题讲清楚",
        script_text="<Person1>欢迎来到 未来学习电台 —— 把复杂问题讲清楚。</Person1>",
    )

    parsed = TypeAdapter(RenderModel).validate_python(render_model.model_dump(mode="json"))

    assert isinstance(parsed, PodcastRenderModel)
    assert parsed.render_type == "podcast_script"


def test_podcast_profile_is_registered_as_direct_content_type() -> None:
    profile = get_content_type_profile("podcast_script")

    assert profile.content_type == "podcast_script"
    assert profile.generation_mode == "direct"
    assert profile.generator_name == "podcast"
    assert profile.exporter_types == ("markdown", "audio")
