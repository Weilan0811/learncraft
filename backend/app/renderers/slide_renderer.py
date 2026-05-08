from app.schemas.elements import ContentElement, ImageElement, MindmapElement
from app.schemas.render import SlidePageModel, SlideRenderModel
from app.schemas.specs import SlideDeckSpec, SlideSpecElement


class SlideRenderer:
    def render(self, spec: SlideDeckSpec, elements: list[ContentElement]) -> SlideRenderModel:
        element_lookup = {element.id: element for element in elements}
        pages = []
        
        for slide in spec.slides:
            page_elements = []
            y_offset = 120
            
            title_element = self._create_text_element(
                id=f"{slide.id}_title",
                content=slide.title,
                top=40,
                font_size=36,
                bold=True,
                height=80,
            )
            page_elements.append(title_element)
            
            body_content = ""
            element_refs = []
            
            for element in slide.elements:
                if element.type == "text" and element.content and element.id != f"{slide.id}_title":
                    body_content += element.content + "\n"
                elif element.type == "element_ref" and element.element_id:
                    element_refs.append(element.element_id)
            
            if body_content.strip():
                body_element = self._create_text_element(
                    id=f"{slide.id}_body",
                    content=body_content.strip(),
                    top=y_offset,
                    font_size=24,
                    bold=False,
                    height=300,
                )
                page_elements.append(body_element)
                y_offset += 200
            
            for ref_id in element_refs:
                element = element_lookup.get(ref_id)
                if element:
                    if isinstance(element, ImageElement):
                        image_element = self._create_image_element(
                            id=element.id,
                            asset_url=element.asset_url,
                            top=y_offset,
                        )
                        page_elements.append(image_element)
                        y_offset += 280
                    elif isinstance(element, MindmapElement):
                        mindmap_element = {
                            "id": element.id,
                            "type": "mindmap",
                            "left": 48,
                            "top": y_offset,
                            "width": 864,
                            "height": 300,
                            "rotate": 0,
                            "content": element.markdown,
                        }
                        page_elements.append(mindmap_element)
                        y_offset += 320
            
            speaker_notes = slide.speaker_notes if slide.speaker_notes else ""
            
            page = {
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
                "layout": slide.layout or "title-content-visual",
                "speakerNotes": speaker_notes,
                "elements": page_elements,
            }
            
            pages.append(SlidePageModel(page=page))
        
        return SlideRenderModel(title=spec.title, pages=pages)
    
    def _create_text_element(self, id: str, content: str, top: int, font_size: int, bold: bool, height: int) -> dict[str, object]:
        return {
            "id": id,
            "type": "text",
            "left": 48,
            "top": top,
            "width": 864,
            "height": height,
            "rotate": 0,
            "content": f"<p>{content}</p>",
            "defaultFontName": "Arial",
            "defaultColor": "#111827",
            "fontSize": font_size,
            "bold": bold,
        }
    
    def _create_image_element(self, id: str, asset_url: str, top: int) -> dict[str, object]:
        return {
            "id": id,
            "type": "image",
            "left": 48,
            "top": top,
            "width": 864,
            "height": 256,
            "rotate": 0,
            "url": asset_url,
        }