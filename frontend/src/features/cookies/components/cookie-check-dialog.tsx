import { useState } from "react";

import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { SuccessMessage } from "@/components/success-message";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useCheckCookieFile } from "@/features/cookies/api";
import type { CookieCheckResult, CookieFile } from "@/features/cookies/types";

interface CookieCheckDialogProps {
  file: CookieFile;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function CheckResult({ result }: { result: CookieCheckResult | undefined }) {
  if (!result) {
    return null;
  }
  if (result.ok) {
    return <SuccessMessage>{result.message}</SuccessMessage>;
  }
  return <FormError message={result.message} />;
}

export function CookieCheckDialog({ file, open, onOpenChange }: CookieCheckDialogProps) {
  const [url, setUrl] = useState("");
  const check = useCheckCookieFile();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    check.mutate({ id: file.id, url: url.trim() });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Test {file.name}</DialogTitle>
          <DialogDescription>
            Opens one page with these cookies, without downloading anything.
          </DialogDescription>
        </DialogHeader>
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          <FormField
            label="Page to open"
            type="url"
            inputMode="url"
            placeholder="https://www.youtube.com/watch?v=…"
            hint="Pick a page that only works when signed in, such as a members-only video."
            value={url}
            onChange={(event) => setUrl(event.target.value)}
          />
          <FormError message={check.isError ? describeError(check.error) : null} />
          <CheckResult result={check.data} />
          <Button type="submit" className="h-10" disabled={check.isPending || !url.trim()}>
            {check.isPending ? "Testing…" : "Test"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
