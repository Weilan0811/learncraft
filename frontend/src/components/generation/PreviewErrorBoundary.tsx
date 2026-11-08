import { Component, type ReactNode } from "react";

interface PreviewErrorBoundaryProps {
  children: ReactNode;
  taskId?: string;
  preview?: object;
}

interface PreviewErrorBoundaryState {
  error?: Error;
}

/**
 * Keeps a renderer crash (e.g. a partial render model with an unexpected
 * shape while units stream in) from unmounting the whole React tree — the
 * progress strip must stay alive during generation.
 */
export class PreviewErrorBoundary extends Component<PreviewErrorBoundaryProps, PreviewErrorBoundaryState> {
  state: PreviewErrorBoundaryState = {};

  static getDerivedStateFromError(error: Error): PreviewErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error("Preview render failed:", error);
  }

  componentDidUpdate(previousProps: PreviewErrorBoundaryProps) {
    if (this.state.error && (previousProps.taskId !== this.props.taskId || previousProps.preview !== this.props.preview)) {
      this.setState({ error: undefined });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <section className="empty-preview">
          <h2>预览渲染中断</h2>
          <p>预览内容渲染时出现异常，生成过程仍在后台继续，进度与导出不受影响。</p>
          <p className="error-text">{this.state.error.message}</p>
          <button type="button" onClick={() => this.setState({ error: undefined })}>
            重新尝试预览
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}
