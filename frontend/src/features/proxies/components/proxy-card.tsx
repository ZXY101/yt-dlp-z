import { FlaskConical, Pencil, Power, Trash2 } from "lucide-react";
import { useState } from "react";

import { describeError } from "@/api/errors";
import { ConfirmButton } from "@/components/confirm-button";
import { FormError } from "@/components/form-error";
import { Button } from "@/components/ui/button";
import { useCheckProxy, useDeleteProxy, useUpdateProxy } from "@/features/proxies/api";
import { ProxyForm } from "@/features/proxies/components/proxy-form";
import { describeProxyStatus } from "@/features/proxies/components/proxy-status";
import type { Proxy } from "@/features/proxies/types";
import { cn } from "@/lib/utils";

function DeleteProxyButton({ proxy }: { proxy: Proxy }) {
  const remove = useDeleteProxy();
  return (
    <ConfirmButton
      trigger={
        <Button variant="ghost" className="h-10" aria-label={`Delete ${proxy.name}`}>
          <Trash2 aria-hidden />
          Delete
        </Button>
      }
      title={`Delete ${proxy.name}?`}
      description="Downloads running through it keep it until they end."
      confirmText="Delete"
      onConfirm={() => remove.mutate(proxy.id)}
    />
  );
}

function ProxyActions({ proxy, onEdit }: { proxy: Proxy; onEdit: () => void }) {
  const check = useCheckProxy();
  const update = useUpdateProxy();
  const failed = [check, update].find((mutation) => mutation.isError);

  function toggle() {
    update.mutate({ id: proxy.id, name: proxy.name, url: null, enabled: !proxy.enabled });
  }

  return (
    <>
      <FormError message={failed ? describeError(failed.error) : null} />
      <div className="flex flex-wrap justify-end gap-2">
        <Button
          variant="ghost"
          className="h-10"
          aria-label={`Test ${proxy.name}`}
          disabled={check.isPending}
          onClick={() => check.mutate(proxy.id)}
        >
          <FlaskConical aria-hidden />
          {check.isPending ? "Testing…" : "Test"}
        </Button>
        <Button variant="ghost" className="h-10" aria-label={`Edit ${proxy.name}`} onClick={onEdit}>
          <Pencil aria-hidden />
          Edit
        </Button>
        <Button
          variant="ghost"
          className="h-10"
          aria-label={`${proxy.enabled ? "Turn off" : "Turn on"} ${proxy.name}`}
          disabled={update.isPending}
          onClick={toggle}
        >
          <Power aria-hidden />
          {proxy.enabled ? "Turn off" : "Turn on"}
        </Button>
        <DeleteProxyButton proxy={proxy} />
      </div>
    </>
  );
}

export function ProxyCard({ proxy }: { proxy: Proxy }) {
  const [editing, setEditing] = useState(false);
  const failed = proxy.enabled && proxy.check_ok === false;
  return (
    <li className="space-y-3 rounded-xl border p-4">
      <div className="min-w-0 space-y-1">
        <p className="truncate font-medium">{proxy.name}</p>
        <p className="font-mono text-xs break-all text-muted-foreground">{proxy.url}</p>
        <p
          className={cn(
            "text-xs break-words",
            failed ? "text-destructive" : "text-muted-foreground",
          )}
        >
          {describeProxyStatus(proxy)}
        </p>
      </div>
      {editing ? (
        <ProxyForm proxy={proxy} onDone={() => setEditing(false)} />
      ) : (
        <ProxyActions proxy={proxy} onEdit={() => setEditing(true)} />
      )}
    </li>
  );
}
