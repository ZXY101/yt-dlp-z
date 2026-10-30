import { useQuery } from "@tanstack/react-query";
import { TriangleAlert } from "lucide-react";

import { api, unwrap } from "@/api/client";
import type { components } from "@/api/generated/schema";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

type SystemInfo = components["schemas"]["SystemInfo"];

export function systemWarnings(info: SystemInfo): string[] {
  const warnings: string[] = [];
  if (info.ytdlp_error) {
    warnings.push(`yt-dlp isn't working: ${info.ytdlp_error}`);
  }
  if (!info.ffmpeg_available) {
    warnings.push("ffmpeg wasn't found. Merging video and audio and converting files won't work.");
  }
  if (!info.deno_available) {
    warnings.push("Deno wasn't found. YouTube downloads may fail or offer fewer formats.");
  }
  return warnings;
}

export function SystemWarnings() {
  const info = useQuery({
    queryKey: ["system"],
    queryFn: () => unwrap(api.GET("/api/system")),
  });
  const warnings = info.data ? systemWarnings(info.data) : [];
  if (warnings.length === 0) {
    return null;
  }
  return (
    <Alert>
      <TriangleAlert aria-hidden />
      <AlertTitle>Setup needs attention</AlertTitle>
      <AlertDescription>
        <ul className="list-disc space-y-1 pl-4">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}
