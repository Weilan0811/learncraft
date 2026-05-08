interface ImageElementProps {
  title: string;
  assetUrl?: string | null;
  altText: string;
}

export function ImageElement({ title, assetUrl, altText }: ImageElementProps) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
  const fullUrl = assetUrl && !assetUrl.startsWith("http") ? `${apiBaseUrl}${assetUrl}` : assetUrl;

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
    </figure>
  );
}
