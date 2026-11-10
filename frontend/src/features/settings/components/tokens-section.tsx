import { KeyRound, Trash2 } from "lucide-react";
import { type FormEvent, useState } from "react";

import { describeError } from "@/api/errors";
import { ConfirmButton } from "@/components/confirm-button";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { RadioOption } from "@/components/radio-option";
import { Button } from "@/components/ui/button";
import { useApiTokens, useCreateApiToken, useRevokeApiToken } from "@/features/settings/tokens-api";
import type { ApiToken, TokenScope } from "@/features/settings/types";

const SCOPE_LABELS: Record<TokenScope, string> = {
  full: "Full access",
  send: "Send links only",
};

function ClaudeCodeCommand({ token }: { token: string }) {
  const url = `${window.location.origin}/mcp`;
  const command = `claude mcp add --transport http yt-dlp-z ${url} --header "Authorization: Bearer ${token}"`;
  return (
    <>
      <p className="text-muted-foreground">To add it to Claude Code:</p>
      <code className="block select-all break-all rounded bg-muted p-2">{command}</code>
    </>
  );
}

function NewToken({ token, scope }: { token: string; scope: TokenScope }) {
  return (
    <div className="space-y-2 rounded-md border p-3 text-sm">
      <p className="font-medium">Copy this token now. It won't be shown again.</p>
      <code className="block select-all break-all rounded bg-muted p-2">{token}</code>
      {scope === "full" && <ClaudeCodeCommand token={token} />}
    </div>
  );
}

function ScopeChoice({
  scope,
  onChange,
}: {
  scope: TokenScope;
  onChange: (scope: TokenScope) => void;
}) {
  return (
    <fieldset className="space-y-1">
      <legend className="mb-1 text-sm font-medium">Access</legend>
      <RadioOption
        name="token-scope"
        label="Full access: everything except managing tokens"
        checked={scope === "full"}
        onSelect={() => onChange("full")}
      />
      <RadioOption
        name="token-scope"
        label="Send links only: check a link and download it with a preset"
        checked={scope === "send"}
        onSelect={() => onChange("send")}
      />
    </fieldset>
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
        <p className="text-sm text-muted-foreground">
          {SCOPE_LABELS[token.scope]} · {lastUsed}
        </p>
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
  const [scope, setScope] = useState<TokenScope>("full");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    create.mutate({ name, scope }, { onSuccess: () => setName("") });
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <FormField
        label="Token name"
        hint="What will use it, e.g. Claude Code."
        value={name}
        onChange={(event) => setName(event.target.value)}
      />
      <ScopeChoice scope={scope} onChange={setScope} />
      <FormError message={create.isError ? describeError(create.error) : null} />
      <Button type="submit" className="h-10" disabled={!name.trim() || create.isPending}>
        <KeyRound aria-hidden />
        Create token
      </Button>
      {create.data && <NewToken token={create.data.token} scope={create.data.scope} />}
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
          Let scripts and AI agents use yt-dlp-z through its API and MCP server. A full-access token
          can do anything except manage tokens, including deleting downloaded files. A send-only
          token can only check links and download them with a preset.
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
