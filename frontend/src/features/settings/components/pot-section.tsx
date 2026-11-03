import { PlugZap } from "lucide-react";
import { useState } from "react";

import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { SuccessMessage } from "@/components/success-message";
import { Button } from "@/components/ui/button";
import {
  usePotProvider,
  useSavePotProvider,
  useTestPotProvider,
} from "@/features/settings/pot-api";
import type { PotProviderInfo } from "@/features/settings/types";

const BGUTIL_URL = "https://github.com/Brainicism/bgutil-ytdlp-pot-provider";

function PotStatus({ info }: { info: PotProviderInfo }) {
  if (!info.url) {
    return <p className="text-sm text-muted-foreground">Off.</p>;
  }
  if (info.error) {
    return <FormError message={`On, but the last check failed: ${info.error}`} />;
  }
  return (
    <p className="text-sm text-muted-foreground">
      On: provider {info.server_version ?? "not checked yet"}, plugin{" "}
      {info.plugin_version ?? "not installed"}.
    </p>
  );
}

function PotMessages({
  info,
  save,
  test,
}: {
  info: PotProviderInfo;
  save: ReturnType<typeof useSavePotProvider>;
  test: ReturnType<typeof useTestPotProvider>;
}) {
  const failed = [save, test].find((mutation) => mutation.isError);
  return (
    <>
      <FormError message={failed ? describeError(failed.error) : null} />
      {save.isSuccess && (
        <SuccessMessage>{info.url ? "PO tokens on." : "PO tokens off."}</SuccessMessage>
      )}
      {test.isSuccess && (
        <SuccessMessage>Provider {test.data.server_version} answered.</SuccessMessage>
      )}
    </>
  );
}

function PotForm({ info }: { info: PotProviderInfo }) {
  const [url, setUrl] = useState(info.url ?? "");
  const save = useSavePotProvider();
  const test = useTestPotProvider();
  const trimmed = url.trim();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    test.reset();
    save.mutate(trimmed || null);
  }

  function runTest() {
    save.reset();
    test.mutate(trimmed);
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit} noValidate>
      <PotStatus info={info} />
      <PotMessages info={info} save={save} test={test} />
      <FormField
        label="Provider address"
        hint="Saving checks the provider and installs the yt-dlp plugin for its version. Empty turns PO tokens off."
        inputMode="url"
        spellCheck={false}
        autoCapitalize="off"
        placeholder="http://bgutil-provider:4416"
        value={url}
        onChange={(event) => setUrl(event.target.value)}
      />
      <div className="flex flex-wrap gap-2">
        <Button type="submit" className="h-10" disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save provider"}
        </Button>
        <Button
          type="button"
          variant="outline"
          className="h-10"
          disabled={test.isPending || !trimmed}
          onClick={runTest}
        >
          <PlugZap aria-hidden />
          {test.isPending ? "Testing…" : "Test"}
        </Button>
      </div>
    </form>
  );
}

/** PO tokens from a bgutil provider, for YouTube formats that need one. */
export function PotSection() {
  const info = usePotProvider();
  return (
    <section className="space-y-4 border-t pt-6" aria-labelledby="pot-heading">
      <div className="space-y-1">
        <h2 id="pot-heading" className="text-lg font-medium">
          PO tokens
        </h2>
        <p className="text-sm text-muted-foreground">
          YouTube asks for a PO token before it serves some formats. Without one, yt-dlp may skip
          formats or fail with HTTP 403. A{" "}
          <a
            href={BGUTIL_URL}
            target="_blank"
            rel="noreferrer"
            className="underline underline-offset-2"
          >
            bgutil provider
          </a>{" "}
          running next to yt-dlp-z makes them.
        </p>
      </div>
      {info.isError && <FormError message={describeError(info.error)} />}
      {info.data && <PotForm info={info.data} />}
    </section>
  );
}
