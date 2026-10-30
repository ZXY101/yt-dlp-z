import { FlaskConical, RefreshCw, Trash2 } from "lucide-react";
import { useRef, useState } from "react";

import { describeError } from "@/api/errors";
import { ConfirmButton } from "@/components/confirm-button";
import { FormError } from "@/components/form-error";
import { Button } from "@/components/ui/button";
import { useDeleteCookieFile, useReplaceCookieFile } from "@/features/cookies/api";
import { CookieCheckDialog } from "@/features/cookies/components/cookie-check-dialog";
import type { CookieFile } from "@/features/cookies/types";

const SHOWN_DOMAINS = 3;

function describeDomains(domains: string[]) {
  const shown = domains.slice(0, SHOWN_DOMAINS).join(", ");
  const hidden = domains.length - SHOWN_DOMAINS;
  return hidden > 0 ? `${shown} and ${hidden} more` : shown;
}

function useCookieActions(file: CookieFile) {
  const replace = useReplaceCookieFile();
  const remove = useDeleteCookieFile();
  const failed = [replace, remove].find((mutation) => mutation.isError);

  async function replaceWith(selected: File | undefined) {
    if (selected) {
      replace.mutate({ id: file.id, name: file.name, content: await selected.text() });
    }
  }

  return { replace, remove, replaceWith, error: failed ? describeError(failed.error) : null };
}

function CookieActions({ file }: { file: CookieFile }) {
  const [checkOpen, setCheckOpen] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const actions = useCookieActions(file);

  return (
    <>
      <FormError message={actions.error} />
      <input
        ref={fileInput}
        type="file"
        accept=".txt,text/plain"
        className="sr-only"
        tabIndex={-1}
        aria-label={`New cookies file for ${file.name}`}
        onChange={(event) => void actions.replaceWith(event.target.files?.[0])}
      />
      <div className="flex flex-wrap justify-end gap-2">
        <Button variant="ghost" className="h-10" onClick={() => setCheckOpen(true)}>
          <FlaskConical aria-hidden />
          Test
        </Button>
        <Button
          variant="ghost"
          className="h-10"
          aria-label={`Replace ${file.name}`}
          disabled={actions.replace.isPending}
          onClick={() => fileInput.current?.click()}
        >
          <RefreshCw aria-hidden />
          Replace
        </Button>
        <ConfirmButton
          trigger={
            <Button variant="ghost" className="h-10" aria-label={`Delete ${file.name}`}>
              <Trash2 aria-hidden />
              Delete
            </Button>
          }
          title={`Delete ${file.name}?`}
          description="Presets using it will download without cookies. This can't be undone."
          confirmText="Delete"
          onConfirm={() => actions.remove.mutate(file.id)}
        />
      </div>
      <CookieCheckDialog file={file} open={checkOpen} onOpenChange={setCheckOpen} />
    </>
  );
}

export function CookieCard({ file }: { file: CookieFile }) {
  const cookieCount = file.cookie_count === 1 ? "1 cookie" : `${file.cookie_count} cookies`;
  return (
    <li className="space-y-3 rounded-xl border p-4">
      <div className="min-w-0 space-y-1">
        <p className="truncate font-medium">{file.name}</p>
        <p className="text-xs break-words text-muted-foreground">
          {cookieCount} for {describeDomains(file.domains)}
        </p>
        <p className="text-xs text-muted-foreground">
          Updated {new Date(file.updated_at).toLocaleString()}
        </p>
      </div>
      <CookieActions file={file} />
    </li>
  );
}
