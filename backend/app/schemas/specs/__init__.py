from app.schemas.specs.common import BaseBlock, ElementReferenceBlock, ElementRequest, RequiredElementSpec, RetryPolicy, TextBlock
from app.schemas.specs.lecture import LectureBlock, LectureSection, LectureSpec
from app.schemas.specs.slide import SlideDeckSpec, SlideLayout, SlideSpecElement, SlideSpecPage

ContentSpec = LectureSpec | SlideDeckSpec
# TODO(content-types): Extend this union when enabling social_post,
# podcast_script, video_script, project_task, quiz_pack, or learning_path.

__all__ = [
    "RetryPolicy",
    "RequiredElementSpec",
    "ElementRequest",
    "BaseBlock",
    "TextBlock",
    "ElementReferenceBlock",
    "LectureBlock",
    "LectureSection",
    "LectureSpec",
    "SlideLayout",
    "SlideSpecElement",
    "SlideSpecPage",
    "SlideDeckSpec",
    "ContentSpec",
]
