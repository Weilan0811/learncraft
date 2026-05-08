'use client';

import type { CSSProperties } from 'react';
import type {
  KitImageElement,
  KitLineElement,
  KitSlideScene,
  KitSceneRendererProps,
  KitShapeElement,
  KitSlideBackground,
  KitSlideElement,
  KitTableCell,
  KitTableElement,
  KitTextElement,
} from '../types';

function joinClassNames(...values: Array<string | undefined>) {
  return values.filter(Boolean).join(' ');
}

function createElementBoxStyle(element: KitSlideElement): CSSProperties {
  return {
    position: 'absolute',
    left: `${element.left}px`,
    top: `${element.top}px`,
    width: `${element.width}px`,
    height: `${element.height}px`,
    transform: `rotate(${element.rotate}deg)`,
    transformOrigin: 'top left',
  };
}

function createShadowStyle(shadow?: { x: number; y: number; blur: number; color: string }) {
  return shadow ? `${shadow.x}px ${shadow.y}px ${shadow.blur}px ${shadow.color}` : undefined;
}

function createOutlineStyle(outline?: { width?: number; color?: string; style?: string }) {
  const width = outline?.width ?? 0;
  if (width <= 0) return undefined;
  return `${width}px ${outline?.style ?? 'solid'} ${outline?.color ?? 'transparent'}`;
}

function createBackgroundStyle(background?: KitSlideBackground, fallback = '#ffffff'): CSSProperties {
  if (!background || background.type === 'solid') {
    return {
      background: background?.color ?? fallback,
    };
  }

  if (background.type === 'image' && background.image) {
    return {
      backgroundImage: `url(${background.image.src})`,
      backgroundSize: background.image.size ?? 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: background.image.size === 'repeat' ? 'repeat' : 'no-repeat',
    };
  }

  if (background.type === 'gradient' && background.gradient) {
    const stops = background.gradient.colors
      .map((stop) => `${stop.color} ${Math.round(stop.pos * 100)}%`)
      .join(', ');

    if (background.gradient.type === 'radial') {
      return { background: `radial-gradient(circle, ${stops})` };
    }

    return {
      background: `linear-gradient(${background.gradient.rotate ?? 0}deg, ${stops})`,
    };
  }

  return { background: fallback };
}

function stripHtml(content: string) {
  return content.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

function renderTextElement(element: KitTextElement) {
  const justifyContent =
    element.verticalAlign === 'middle'
      ? 'center'
      : element.verticalAlign === 'bottom'
        ? 'flex-end'
        : 'flex-start';

  return (
    <div
      key={element.id}
      className="scenekit-slide__text"
      style={{
        ...createElementBoxStyle(element),
        display: 'flex',
        flexDirection: 'column',
        justifyContent,
        padding: element.fill && element.fill !== 'transparent' ? '8px 12px' : undefined,
        color: element.defaultColor,
        fontFamily: element.defaultFontName,
        fontSize: element.fontSize ? `${element.fontSize}px` : undefined,
        fontWeight: element.bold ? 700 : undefined,
        fontStyle: element.italic ? 'italic' : undefined,
        textDecoration: element.underline ? 'underline' : undefined,
        textAlign: element.align,
        background: element.fill,
        opacity: element.opacity,
        lineHeight: element.lineHeight,
        border: createOutlineStyle(element.outline),
        borderRadius: element.radius ? `${element.radius}px` : undefined,
        boxShadow: createShadowStyle(element.shadow),
      }}
      dangerouslySetInnerHTML={{ __html: element.content }}
    />
  );
}

function renderImageElement(element: KitImageElement) {
  return (
    <img
      key={element.id}
      className="scenekit-slide__image"
      style={{
        ...createElementBoxStyle(element),
        objectFit: 'cover',
        borderRadius: element.radius ? `${element.radius}px` : undefined,
        opacity: element.opacity,
        boxShadow: createShadowStyle(element.shadow),
      }}
      src={element.src}
      alt={element.name ?? element.id}
    />
  );
}

function renderShapeElement(element: KitShapeElement) {
  const borderRadius =
    element.shape === 'ellipse'
      ? '9999px'
      : element.shape === 'roundRect'
        ? `${element.radius ?? 18}px`
        : element.radius
          ? `${element.radius}px`
          : undefined;

  return (
    <div
      key={element.id}
      className="scenekit-slide__shape"
      style={{
        ...createElementBoxStyle(element),
        background: element.fill ?? '#cbd5e1',
        opacity: element.opacity ?? 1,
        border: createOutlineStyle(element.outline),
        borderRadius,
        boxShadow: createShadowStyle(element.shadow),
      }}
      aria-label={element.name ?? element.id}
    />
  );
}

function renderLineElement(element: KitLineElement) {
  const deltaX = element.end[0] - element.start[0];
  const deltaY = element.end[1] - element.start[1];
  const length = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
  const angle = (Math.atan2(deltaY, deltaX) * 180) / Math.PI;

  return (
    <div
      key={element.id}
      className="scenekit-slide__line"
      style={{
        position: 'absolute',
        left: `${element.left + element.start[0]}px`,
        top: `${element.top + element.start[1]}px`,
        width: `${length}px`,
        borderTop: `${element.strokeWidth ?? 2}px ${element.style ?? 'solid'} ${element.color}`,
        transform: `rotate(${angle}deg)`,
        transformOrigin: 'top left',
      }}
      aria-hidden="true"
    />
  );
}

function renderTableCell(cell: KitTableCell) {
  return (
    <td
      key={cell.id}
      colSpan={cell.colspan}
      rowSpan={cell.rowspan}
      style={{
        padding: '10px 12px',
        border: '1px solid #cbd5e1',
        background: cell.style?.backcolor,
        color: cell.style?.color,
        textAlign: cell.style?.align,
        fontWeight: cell.style?.bold ? 700 : 400,
        fontStyle: cell.style?.italic ? 'italic' : undefined,
        fontSize: cell.style?.fontSize ? `${cell.style.fontSize}px` : undefined,
      }}
    >
      {cell.text}
    </td>
  );
}

function renderTableElement(element: KitTableElement) {
  return (
    <div
      key={element.id}
      className="scenekit-slide__table"
      style={{
        ...createElementBoxStyle(element),
        border: createOutlineStyle(element.outline),
        fontFamily: element.fontName,
        fontSize: element.fontSize ? `${element.fontSize}px` : undefined,
        color: element.textColor,
      }}
    >
      <table>
        <tbody>
          {element.data.map((row, rowIndex) => (
            <tr key={`${element.id}-row-${rowIndex}`}>{row.map(renderTableCell)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderUnsupportedElement(element: KitSlideElement) {
  return (
    <div key={element.id} className="scenekit-slide__unsupported" style={createElementBoxStyle(element)}>
      Unsupported element: {element.type}
    </div>
  );
}

function renderElement(element: KitSlideElement) {
  switch (element.type) {
    case 'text':
      return renderTextElement(element);
    case 'image':
      return renderImageElement(element);
    case 'shape':
      return renderShapeElement(element);
    case 'line':
      return renderLineElement(element);
    case 'table':
      return renderTableElement(element);
    default:
      return renderUnsupportedElement(element);
  }
}

type SlideSceneProps = Omit<KitSceneRendererProps, 'scene'> & {
  scene: KitSlideScene;
};

export function SlideScene({ scene, className, style }: SlideSceneProps) {
  const { canvas } = scene.content;
  const viewportHeight = Math.round(canvas.viewportSize / canvas.viewportRatio);
  const backgroundStyle = createBackgroundStyle(canvas.background, canvas.theme.backgroundColor);

  return (
    <section className={joinClassNames('scenekit-slide-shell', className)} style={style}>
      <div
        className="scenekit-slide"
        style={{
          width: `${canvas.viewportSize}px`,
          height: `${viewportHeight}px`,
          color: canvas.theme.fontColor,
          fontFamily: canvas.theme.fontName,
          ...backgroundStyle,
        }}
        aria-label={scene.title}
      >
        <div className="scenekit-slide__meta">
          <span className="scenekit-slide__badge">Slide</span>
          <h2>{scene.title}</h2>
        </div>
        {canvas.elements.map(renderElement)}
        {!canvas.elements.length && (
          <div className="scenekit-slide__empty">{stripHtml(scene.title) || 'Empty slide'}</div>
        )}
      </div>
    </section>
  );
}
