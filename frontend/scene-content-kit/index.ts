export { SceneRenderer } from './src/components/scene-renderer';
export { SlideScene } from './src/components/slide-scene';
export { adaptOpenMAICScene, adaptOpenMAICScenes, isPortableSceneType } from './src/adapters/openmaic';
export { createSlideScene } from './src/factories/slide';
export type {
  CreateSlideSceneOptions,
  KitBaseElement,
  KitElementOutline,
  KitElementShadow,
  KitScene,
  KitSceneContent,
  KitSceneType,
  KitSceneRendererProps,
  KitSlideBackground,
  KitSlideContent,
  KitSlideElement,
  KitSlideScene,
  KitSlideSceneData,
  KitTableCell,
  KitTheme,
  OpenMAICSceneLike,
} from './src/types';
