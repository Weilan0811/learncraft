'use client';

import type { KitSceneRendererProps, KitSlideScene } from '../types';
import { SlideScene } from './slide-scene';

export function SceneRenderer(props: KitSceneRendererProps) {
  const { scene, emptyState } = props;

  if (scene.type === 'slide' && scene.content.type === 'slide') {
    return <SlideScene {...props} scene={scene as KitSlideScene} />;
  }

  return emptyState ? <>{emptyState}</> : null;
}
