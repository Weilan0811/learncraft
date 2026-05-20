import { ContentGenerationPage } from "./pages/ContentGenerationPage";
import { FullscreenPreviewPage } from "./pages/FullscreenPreviewPage";

export default function App() {
  const isFullscreen = new URLSearchParams(window.location.search).has("fullscreen");

  if (isFullscreen) {
    return <FullscreenPreviewPage />;
  }

  return <ContentGenerationPage />;
}
