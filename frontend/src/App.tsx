import { useEffect, useState } from "react";

import { LineIcon } from "./components/generation/icons";
import { useContentGenerationStore } from "./stores/contentGenerationStore";
import { ContentGenerationPage } from "./pages/ContentGenerationPage";
import { FullscreenPreviewPage } from "./pages/FullscreenPreviewPage";
import { TaskHistoryPage } from "./pages/TaskHistoryPage";

type ServiceState = "checking" | "online" | "offline";
type View = "create" | "history";

interface Route {
  view: View;
  taskId?: string;
}

function readRoute(): Route {
  const hash = window.location.hash;
  if (hash === "#history") {
    return { view: "history" };
  }
  if (hash.startsWith("#task=")) {
    const taskId = decodeURIComponent(hash.slice("#task=".length)).trim();
    return { view: "create", taskId: taskId || undefined };
  }
  return { view: "create" };
}

export default function App() {
  const isFullscreen = new URLSearchParams(window.location.search).has("fullscreen");

  if (isFullscreen) {
    return <FullscreenPreviewPage />;
  }

  return <WorkbenchApp />;
}

function WorkbenchApp() {
  const [route, setRoute] = useState<Route>(readRoute);
  const [serviceState, setServiceState] = useState<ServiceState>("checking");
  const loadPreviewByTaskId = useContentGenerationStore((state) => state.loadPreviewByTaskId);
  const stopStreamRefresh = useContentGenerationStore((state) => state.stopStreamRefresh);

  useEffect(() => {
    const applyRoute = () => {
      const next = readRoute();
      setRoute(next);
      if (next.view === "history") {
        stopStreamRefresh();
      } else if (next.taskId) {
        void loadPreviewByTaskId(next.taskId);
      } else {
        const state = useContentGenerationStore.getState();
        if (state.task?.status === "queued" || state.task?.status === "running") {
          state.trackTask(state.task.task_id);
        }
        void state.loadFailedResources();
      }
    };
    applyRoute();
    window.addEventListener("hashchange", applyRoute);
    return () => window.removeEventListener("hashchange", applyRoute);
  }, [loadPreviewByTaskId, stopStreamRefresh]);

  useEffect(() => () => stopStreamRefresh(), [stopStreamRefresh]);

  useEffect(() => {
    let active = true;
    fetch("/health")
      .then((response) => {
        if (active) {
          setServiceState(response.ok ? "online" : "offline");
        }
      })
      .catch(() => {
        if (active) {
          setServiceState("offline");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  function navigate(view: View) {
    const hash = view === "history" ? "#history" : "#create";
    if (window.location.hash === hash) {
      setRoute({ view });
      return;
    }
    window.location.hash = hash;
  }

  const serviceLabel =
    serviceState === "online" ? "服务正常" : serviceState === "offline" ? "服务不可用" : "检查中";

  return (
    <main className="app-shell">
      <header className="workbench-header">
        <div className="brand-lockup">
          <span className="brand-mark">
            <LineIcon name="brand" size={16} />
          </span>
          <h1>内容生成工作台</h1>
          <span className="brand-divider" aria-hidden />
          <p className="brand-subtitle">基于大模型的教学内容创作工具</p>
        </div>
        <nav className="app-nav" aria-label="主导航">
          <button
            type="button"
            className={`app-nav-button${route.view === "create" ? " is-active" : ""}`}
            aria-current={route.view === "create" ? "page" : undefined}
            onClick={() => navigate("create")}
          >
            内容生成
          </button>
          <button
            type="button"
            className={`app-nav-button${route.view === "history" ? " is-active" : ""}`}
            aria-current={route.view === "history" ? "page" : undefined}
            onClick={() => navigate("history")}
          >
            历史记录
          </button>
        </nav>
        <div className={`service-status service-status--${serviceState}`}>
          <span className="service-dot" aria-hidden />
          <span>{serviceLabel}</span>
        </div>
      </header>

      {route.view === "history" ? <TaskHistoryPage /> : <ContentGenerationPage />}
    </main>
  );
}
