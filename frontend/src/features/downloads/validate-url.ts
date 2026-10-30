export function validateUrl(url: string): string | undefined {
  const trimmed = url.trim();
  if (!trimmed) {
    return "Paste a link to a video, playlist or channel.";
  }
  if (!/^https?:\/\/\S+$/i.test(trimmed)) {
    return "Use a full link starting with http:// or https://.";
  }
  return undefined;
}
