import { useContentGenerationStore } from "../../stores/contentGenerationStore";
import { ResourceIssueNotice } from "../generation/ResourceIssueNotice";

interface ImageElementProps {
  title: string;
  assetUrl?: string | null;
  altText: string;
  resourceKey?: string;
}

export function ImageElement({ title, assetUrl, altText, resourceKey }: ImageElementProps) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
  const fullUrl = assetUrl && !assetUrl.startsWith("http") ? `${apiBaseUrl}${assetUrl}` : assetUrl;
  const issue = useContentGenerationStore((state) =>
    resourceKey
      ? state.failedResources.find(
          (resource) => resource.asset_type === "image" && resource.resource_key === resourceKey
        )
      : undefined
  );

  return (
    <figure className="content-block image-element">
      <div className="image-frame">
        {fullUrl ? (
          <img src={fullUrl} alt={altText} loading="lazy" />
        ) : (
          <div className="image-placeholder-text">图片资源占位</div>
        )}
      </div>
      <figcaption>
        <strong>{title}</strong>
      </figcaption>
      {issue ? <ResourceIssueNotice resource={issue} /> : null}
    </figure>
  );
}
