import { KeyRound, Trash2 } from "lucide-react";
import { type FormEvent, useState } from "react";

import { describeError } from "@/api/errors";
import { ConfirmButton } from "@/components/confirm-button";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { useApiTokens, useCreateApiToken, useRevokeApiToken } from "@/features/settings/tokens-api";
import type { ApiToken } from "@/features/settings/types";

function NewToken({ token }: { token: string }) {
  const url = `${window.location.origin}/mcp`;
  const command = `claude mcp add --transport http yt-dlp-z ${url} --header "Authorization: Bearer ${token}"`;
  return (
    <div className="space-y-2 rounded-md border p-3 text-sm">
      <p className="font-medium">Copy this token now. It won't be shown again.</p>
      <code className="block select-all break-all rounded bg-muted p-2">{token}</code>
      <p className="text-muted-foreground">To add it to Claude Code:</p>
      <code className="block select-all break-all rounded bg-muted p-2">{command}</code>
    </div>
  );
}

function TokenRow({ token }: { token: ApiToken }) {
  const revoke = useRevokeApiToken();
  const lastUsed = token.last_used_at
    ? `Last used ${new Date(token.last_used_at).toLocaleString()}`
    : "Never used";
  return (
    <li className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3">
      <div className="min-w-0">
        <p className="break-words font-medium">{token.name}</p>
        <p className="text-sm text-muted-foreground">{lastUsed}</p>
        <FormError message={revoke.isError ? describeError(revoke.error) : null} />
      </div>
      <ConfirmButton
        trigger={
          <Button variant="ghost" className="h-10" aria-label={`Revoke ${token.name}`}>
            <Trash2 aria-hidden />
            Revoke
          </Button>
        }
        title={`Revoke ${token.name}?`}
        description="Anything using this token loses access straight away."
        confirmText="Revoke"
        onConfirm={() => revoke.mutate(token.id)}
      />
    </li>
  );
}

function CreateTokenForm() {
  const create = useCreateApiToken();
  const [name, setName] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    create.mutate(name, { onSuccess: () => setName("") });
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <FormField
        label="Token name"
        hint="What will use it, e.g. Claude Code."
        value={name}
        onChange={(event) => setName(event.target.value)}
      />
      <FormError message={create.isError ? describeError(create.error) : null} />
      <Button type="submit" className="h-10" disabled={!name.trim() || create.isPending}>
        <KeyRound aria-hidden />
        Create token
      </Button>
      {create.data && <NewToken token={create.data.token} />}
    </form>
  );
}

export function TokensSection() {
  const tokens = useApiTokens();
  return (
    <section className="space-y-4 border-t pt-6" aria-labelledby="tokens-heading">
      <div className="space-y-1">
        <h2 id="tokens-heading" className="text-lg font-medium">
          API tokens
        </h2>
        <p className="text-sm text-muted-foreground">
          Let scripts and AI agents use yt-dlp-z through its API and MCP server. A token can do
          anything except manage tokens, including deleting downloaded files.
        </p>
      </div>
      {tokens.isError && <FormError message={describeError(tokens.error)} />}
      {tokens.data && tokens.data.length > 0 && (
        <ul className="space-y-2">
          {tokens.data.map((token) => (
            <TokenRow key={token.id} token={token} />
          ))}
        </ul>
      )}
      <CreateTokenForm />
    </section>
  );
}
