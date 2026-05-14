export interface PodcastAudioSegment {
  segment_id: string;
  order: number;
  speaker: "Person1" | "Person2";
  voice: "Ethan" | "Cherry";
  text: string;
  audio_url?: string | null;
  status: "pending" | "generated" | "failed";
  error_message?: string | null;
  retry_count?: number;
}

export interface PodcastAudioAsset {
  id: string;
  type: "audio_file";
  title: string;
  speaker: "Person1" | "Person2";
  voice: "Ethan" | "Cherry";
  audio_url: string;
  format: string;
  duration_seconds?: number | null;
  byte_size?: number | null;
  order: number;
}

export interface PodcastRenderModel {
  render_type: "podcast_script";
  content_type: "podcast_script";
  title: string;
  podcast_name: string;
  podcast_tagline: string;
  script_text: string;
  segments: PodcastAudioSegment[];
  audio_assets: PodcastAudioAsset[];
  audio_manifest_url?: string | null;
  final_audio_url?: string | null;
  warnings: string[];
}
