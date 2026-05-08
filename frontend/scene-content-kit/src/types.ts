import type { CSSProperties, ReactNode } from 'react';

export type KitSceneType = 'slide';

export interface KitScene {
  id: string;
  title: string;
  type: KitSceneType;
  order?: number;
  content: KitSlideContent;
}

export type KitSceneContent = KitSlideContent;
export type KitSlideScene = KitScene;

export interface KitTheme {
  backgroundColor: string;
  themeColors: string[];
  fontColor: string;
  fontName: string;
}

export interface KitSlideBackground {
  type: 'solid' | 'gradient' | 'image';
  color?: string;
  image?: {
    src: string;
    size?: 'cover' | 'contain' | 'repeat';
  };
  gradient?: {
    type: 'linear' | 'radial';
    rotate?: number;
    colors: Array<{ pos: number; color: string }>;
  };
}

export interface KitElementShadow {
  x: number;
  y: number;
  blur: number;
  color: string;
}

export interface KitElementOutline {
  width?: number;
  color?: string;
  style?: 'solid' | 'dashed' | 'dotted';
}

export interface KitBaseElement {
  id: string;
  type: string;
  left: number;
  top: number;
  width: number;
  height: number;
  rotate: number;
  name?: string;
}

export interface KitTextElement extends KitBaseElement {
  type: 'text';
  content: string;
  defaultFontName?: string;
  defaultColor?: string;
  fontSize?: number;
  bold?: boolean;
  italic?: boolean;
  underline?: boolean;
  align?: 'left' | 'center' | 'right' | 'justify';
  verticalAlign?: 'top' | 'middle' | 'bottom';
  fill?: string;
  opacity?: number;
  lineHeight?: number;
  radius?: number;
  outline?: KitElementOutline;
  shadow?: KitElementShadow;
}

export interface KitImageElement extends KitBaseElement {
  type: 'image';
  src: string;
  fixedRatio?: boolean;
  radius?: number;
  opacity?: number;
  shadow?: KitElementShadow;
}

export interface KitShapeElement extends KitBaseElement {
  type: 'shape';
  shape?: 'rect' | 'roundRect' | 'ellipse';
  fill?: string;
  opacity?: number;
  radius?: number;
  outline?: KitElementOutline;
  shadow?: KitElementShadow;
}

export interface KitLineElement extends KitBaseElement {
  type: 'line';
  start: [number, number];
  end: [number, number];
  color: string;
  style?: 'solid' | 'dashed' | 'dotted';
  strokeWidth?: number;
}

export interface KitTableCell {
  id: string;
  text: string;
  colspan?: number;
  rowspan?: number;
  style?: {
    bold?: boolean;
    italic?: boolean;
    color?: string;
    backcolor?: string;
    align?: 'left' | 'center' | 'right' | 'justify';
    fontSize?: number;
  };
}

export interface KitTableElement extends KitBaseElement {
  type: 'table';
  data: KitTableCell[][];
  outline?: KitElementOutline;
  fontSize?: number;
  fontName?: string;
  textColor?: string;
}

export type KitSlideElement =
  | KitTextElement
  | KitImageElement
  | KitShapeElement
  | KitLineElement
  | KitTableElement;

export interface KitSlideSceneData {
  id: string;
  viewportSize: number;
  viewportRatio: number;
  theme: KitTheme;
  elements: KitSlideElement[];
  background?: KitSlideBackground;
}

export interface KitSlideContent {
  type: 'slide';
  canvas: KitSlideSceneData;
}

export interface CreateSlideSceneOptions {
  id?: string;
  title?: string;
  order?: number;
}

export interface KitSceneRendererProps {
  scene: KitScene;
  className?: string;
  style?: CSSProperties;
  emptyState?: ReactNode;
}

export interface OpenMAICSceneLike {
  id: string;
  title: string;
  type: string;
  order?: number;
  stageId?: string;
  content: unknown;
}
