# Scene Content Kit

本组件采用 MIT，基于 OpenMAIC 相关实现简化和封装。来源与改动见 [ORIGIN.md](ORIGIN.md)，上游版权及许可声明见 [LICENSE.OpenMAIC](LICENSE.OpenMAIC)。

`scene-content-kit` is a lightweight slide-only renderer extracted from OpenMAIC. It is designed for Next.js applications that need to render static PPT-like pages from structured JSON.

## What It Does

The current package focuses only on `slide` pages:

- Render one slide from `KitSlideSceneData`
- Wrap slide JSON with `createSlideScene(...)`
- Render with `SceneRenderer`
- Adapt existing OpenMAIC slide scenes with `adaptOpenMAICScene(...)`
- Preview a multi-page JSON deck in the demo route

Quiz, playback, whiteboard, animation, video, audio, and full editing features are intentionally excluded to keep the package small and easy to reuse.

## Supported Static Elements

The slide renderer currently supports:

- `text`: HTML text, font family, font size, color, bold, italic, underline, alignment, vertical alignment, fill, border, radius, opacity, shadow
- `image`: image source, size, radius, opacity, shadow
- `shape`: rectangle, rounded rectangle, ellipse, fill, border, opacity, radius, shadow
- `line`: start/end points, color, width, solid/dashed/dotted styles
- `table`: text matrix, basic cell styling, merged cells, table outline

Unsupported or complex PPT content should be rasterized by the converter and emitted as an `image`.

## Files

- `index.ts`: public exports
- `styles.css`: slide-only reusable styles
- `src/types.ts`: portable slide contracts
- `src/factories/slide.ts`: `createSlideScene(...)`
- `src/adapters/openmaic.ts`: OpenMAIC slide adapter
- `src/components/scene-renderer.tsx`: public renderer entry point
- `src/components/slide-scene.tsx`: static slide renderer
- `docs/ppt-slide-json-spec-v1.md`: intermediate JSON specification
- `docs/ppt-converter-implementation-guide.md`: converter implementation guide
- `docs/example-slide-v1.json`: single-page example
- `docs/example-deck-v1.json`: multi-page preview example

## Quick Usage

Import the CSS once in your Next.js app:

```tsx
import '@/scene-content-kit/styles.css';
```

Render one structured slide file:

```tsx
import slideJson from './ppt-slide.json';
import {
  SceneRenderer,
  createSlideScene,
  type KitSlideSceneData,
} from '@/scene-content-kit';

const page = slideJson.page;

const canvas: KitSlideSceneData = {
  id: page.id,
  viewportSize: page.width,
  viewportRatio: page.width / page.height,
  theme: page.theme,
  background: page.background,
  elements: page.elements,
};

const scene = createSlideScene(canvas, {
  id: page.id,
  title: page.title,
});

export default function PPTPreviewPage() {
  return <SceneRenderer scene={scene} />;
}
```

## Expected JSON Shape

The recommended converter output is documented in [`docs/ppt-slide-json-spec-v1.md`](./docs/ppt-slide-json-spec-v1.md).

Minimal example:

```json
{
  "version": "scenekit.slide/v1",
  "page": {
    "id": "slide-001",
    "title": "PPT Page 1",
    "width": 960,
    "height": 540,
    "background": {
      "type": "solid",
      "color": "#ffffff"
    },
    "theme": {
      "backgroundColor": "#ffffff",
      "themeColors": ["#2563eb", "#0f766e"],
      "fontColor": "#111827",
      "fontName": "Arial"
    },
    "elements": [
      {
        "id": "title-1",
        "type": "text",
        "left": 48,
        "top": 40,
        "width": 600,
        "height": 80,
        "rotate": 0,
        "content": "<p>Imported PPT Slide</p>",
        "defaultFontName": "Arial",
        "defaultColor": "#111827",
        "fontSize": 36,
        "bold": true
      }
    ]
  }
}
```

## Preview Demo

A minimal multi-page preview route is included in the repository:

```text
/scene-content-kit-preview
```

It reads:

```text
scene-content-kit/docs/example-deck-v1.json
```

and renders each page through `SceneRenderer`. Replace that JSON with PPT converter output to test restoration quality.

## OpenMAIC Adapter

If you already have an OpenMAIC slide scene:

```tsx
import { SceneRenderer, adaptOpenMAICScene } from '@/scene-content-kit';

export function PortableSlide({ openmaicScene }: { openmaicScene: unknown }) {
  const scene = adaptOpenMAICScene(openmaicScene as Parameters<typeof adaptOpenMAICScene>[0]);
  return <SceneRenderer scene={scene} />;
}
```

Only `slide` scenes are accepted. Non-slide scenes are rejected to keep this package slide-only.

## Integration Notes

- This package renders static pages only.
- Dynamic media and animations should be omitted or rasterized in the converter.
- Complex charts, SmartArt, and freeform shapes should be exported as images for v1.
- The component does not depend on OpenMAIC stores, playback engines, or Tailwind utilities.
