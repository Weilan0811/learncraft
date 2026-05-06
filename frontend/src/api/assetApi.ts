import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? ""
});
// TODO(MVP-assets): Add helpers for signed download URLs, image preview
// metadata, PDF downloads, slide JSON downloads, and asset bundle exports.

export async function getAsset(assetId: string): Promise<Record<string, unknown>> {
  const { data } = await api.get<Record<string, unknown>>(`/api/assets/${assetId}`);
  return data;
}
