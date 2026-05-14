import type { PodcastRenderModel } from "../../../types/podcast";

interface PodcastRendererProps {
  model: PodcastRenderModel;
}

function speakerLabel(speaker: "Person1" | "Person2", voice: "Ethan" | "Cherry") {
  return speaker === "Person1" ? `Person1 / ${voice}` : `Person2 / ${voice}`;
}

export function PodcastRenderer({ model }: PodcastRendererProps) {
  return (
    <article className="podcast-renderer">
      <header className="podcast-header">
        <div>
          <p className="eyebrow">Podcast</p>
          <h2>{model.title}</h2>
          <p>
            {model.podcast_name} —— {model.podcast_tagline}
          </p>
        </div>
        <div className="voice-map">
          <span>Person1 / Ethan</span>
          <span>Person2 / Cherry</span>
        </div>
      </header>

      {model.final_audio_url ? (
        <section className="podcast-player">
          <h3>完整音频</h3>
          <audio controls src={model.final_audio_url} />
        </section>
      ) : null}

      <section className="podcast-segments">
        <h3>分段音频</h3>
        {model.segments.map((segment) => (
          <div className="podcast-segment" key={segment.segment_id}>
            <div className="segment-meta">
              <strong>{speakerLabel(segment.speaker, segment.voice)}</strong>
              <span>
                {segment.status}
                {segment.retry_count ? ` · retry ${segment.retry_count}` : ""}
              </span>
            </div>
            <p>{segment.text}</p>
            {segment.audio_url ? <audio controls src={segment.audio_url} /> : null}
            {segment.error_message ? <p className="error-text">{segment.error_message}</p> : null}
          </div>
        ))}
      </section>

      {model.audio_manifest_url ? (
        <a className="manifest-link" href={model.audio_manifest_url}>
          Download Audio Manifest
        </a>
      ) : null}
    </article>
  );
}
