import React, { useEffect, useState } from "react";
import { InteractiveHtmlRenderer } from "../components/renderers/InteractiveHtmlRenderer";
import { getContentGenerationPreview } from "../api/contentGenerationApi";
import type { InteractiveHtmlRenderModel } from "../types/interactiveHtml";

export const FullscreenPreviewPage: React.FC = () => {
  const [model, setModel] = useState<InteractiveHtmlRenderModel | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const taskId = params.get("fullscreen");
    if (!taskId) {
      setError("No task ID provided. Use ?fullscreen=<taskId> in the URL.");
      return;
    }

    getContentGenerationPreview(taskId.trim())
      .then((preview) => {
        if (preview.render_model.render_type === "interactive_html_page") {
          setModel(preview.render_model as InteractiveHtmlRenderModel);
          document.title = preview.render_model.title || "Interactive Lesson";
        } else {
          setError("This task does not contain an interactive HTML lesson.");
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load preview");
      });
  }, []);

  if (error) {
    return (
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        minHeight: "100vh", fontFamily: "system-ui, sans-serif",
        color: "#667085", fontSize: "16px"
      }}>
        {error}
      </div>
    );
  }

  if (!model) {
    return (
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        minHeight: "100vh", fontFamily: "system-ui, sans-serif",
        color: "#667085", fontSize: "16px"
      }}>
        Loading...
      </div>
    );
  }

  return <InteractiveHtmlRenderer model={model} fullscreen />;
};

export default FullscreenPreviewPage;
