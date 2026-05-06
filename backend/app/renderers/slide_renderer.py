from app.schemas.elements import ContentElement
from app.schemas.render import SlidePageModel, SlideRenderModel
from app.schemas.specs import SlideDeckSpec


class SlideRenderer:
    def render(self, spec: SlideDeckSpec, elements: list[ContentElement]) -> SlideRenderModel:
        # TODO(MVP-slide-renderer): Convert SlideDeckSpec into full
        # scene-content-kit JSON, including images, tables, theme, and layouts.
        pages = [
            SlidePageModel(
                page={
                    "id": slide.id,
                    "title": slide.title,
                    "width": 960,
                    "height": 540,
                    "background": {"type": "solid", "color": "#ffffff"},
                    "theme": {
                        "backgroundColor": "#ffffff",
                        "themeColors": ["#2563eb", "#0f766e"],
                        "fontColor": "#111827",
                        "fontName": "Arial",
                    },
                    "elements": [
                        {
                            "id": f"{slide.id}_title",
                            "type": "text",
                            "left": 48,
                            "top": 40,
                            "width": 720,
                            "height": 80,
                            "rotate": 0,
                            "content": f"<p>{slide.title}</p>",
                            "defaultFontName": "Arial",
                            "defaultColor": "#111827",
                            "fontSize": 36,
                            "bold": True,
                        }
                    ],
                }
            )
            for slide in spec.slides
        ]
        return SlideRenderModel(title=spec.title, pages=pages)
