interface ImageElementProps {
  title: string;
  assetUrl?: string | null;
  altText: string;
}

export function ImageElement({ title, assetUrl, altText }: ImageElementProps) {
  // TODO(MVP-image): Load real generated image URLs, show loading/error
  // placeholders, support click-to-zoom, and preserve alt_text for accessibility.
  return (
    <figure className="content-block image-placeholder">
      <div className="image-frame">{assetUrl ? <span>{assetUrl}</span> : <span>图片资源占位</span>}</div>
      <figcaption>
        <strong>{title}</strong>
        <span>{altText}</span>
      </figcaption>
    </figure>
  );
}
