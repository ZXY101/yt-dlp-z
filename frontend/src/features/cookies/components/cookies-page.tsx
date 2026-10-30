import type { UseQueryResult } from "@tanstack/react-query";
import { Cookie } from "lucide-react";

import { describeError } from "@/api/errors";
import { EmptyState } from "@/components/empty-state";
import { FormError } from "@/components/form-error";
import { PageHeader } from "@/components/page-header";
import { useCookieFiles } from "@/features/cookies/api";
import { CookieCard } from "@/features/cookies/components/cookie-card";
import { CookieUploadForm } from "@/features/cookies/components/cookie-upload-form";
import type { CookieFile } from "@/features/cookies/types";

const UPLOAD_FORM_ID = "cookie-upload";

/** Focusing the form's first field also scrolls it into view. */
function focusUploadForm() {
  document.getElementById(UPLOAD_FORM_ID)?.querySelector("input")?.focus();
}

function CookieList({ files }: { files: UseQueryResult<CookieFile[]> }) {
  if (files.isPending) {
    return <p className="text-sm text-muted-foreground">Loading cookies…</p>;
  }
  if (files.isError) {
    return <FormError message={describeError(files.error)} />;
  }
  if (files.data.length === 0) {
    return (
      <EmptyState
        icon={Cookie}
        title="No cookies yet"
        description="Downloads run signed out until you add a cookies file."
        action={{ label: "Add a cookies file", onClick: focusUploadForm }}
      />
    );
  }
  return (
    <ul className="space-y-3" aria-label="Cookies files">
      {files.data.map((file) => (
        <CookieCard key={file.id} file={file} />
      ))}
    </ul>
  );
}

export function CookiesPage() {
  const files = useCookieFiles();
  return (
    <>
      <PageHeader title="Cookies" />
      <p className="text-sm text-muted-foreground">
        Cookies let yt-dlp download as you: members-only, private and age-restricted videos. Export
        them from a browser where you're signed in. They're stored privately on the server and never
        shown again.
      </p>
      <CookieUploadForm id={UPLOAD_FORM_ID} />
      <CookieList files={files} />
    </>
  );
}
