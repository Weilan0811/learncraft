import { ResourceIssueNotice } from "../../generation/ResourceIssueNotice";
import { useContentGenerationStore } from "../../../stores/contentGenerationStore";
import type { SocialPostRenderModel } from "../../../types/socialPost";

interface SocialPostPreviewRendererProps {
  model: SocialPostRenderModel;
}

export function SocialPostPreviewRenderer({ model }: SocialPostPreviewRendererProps) {
  const assets = model.preview_assets.filter((asset) => asset.local_path || asset.public_url || asset.wechat_url);
  const failedResources = useContentGenerationStore((state) => state.failedResources);

  return (
    <section className="social-post-renderer">
      <header className="social-post-header">
        <div>
          <p className="eyebrow">WeChat Article</p>
          <h2>{model.title}</h2>
          <p>{model.digest}</p>
        </div>
        <span className="template-pill">{model.template}</span>
      </header>

      {model.warnings.length > 0 ? (
        <div className="social-post-warnings">
          {model.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      <div className="phone-preview-shell">
        <iframe title={model.title} sandbox="" srcDoc={model.html} />
      </div>

      {assets.length > 0 ? (
        <div className="social-post-assets">
          <h3>Preview assets</h3>
          <ul>
            {assets.map((asset) => {
              const issue = failedResources.find(
                (resource) => resource.asset_type === "image" && resource.slot_id === asset.slot_id
              );
              return (
                <li key={asset.slot_id}>
                  <strong>{asset.slot_id}</strong>
                  <span>{asset.caption}</span>
                  {issue ? <ResourceIssueNotice resource={issue} /> : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
