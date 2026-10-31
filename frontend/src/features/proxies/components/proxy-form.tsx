import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { useProxyForm } from "@/features/proxies/hooks/use-proxy-form";
import type { Proxy } from "@/features/proxies/types";

const ADDRESS_HINT =
  "http://, https://, socks4:// or socks5:// with the host and port. Add user:password@ before the host if the proxy needs a login.";

interface ProxyFormProps {
  /** The proxy to edit; null adds a new one. */
  proxy: Proxy | null;
  onDone: () => void;
}

export function ProxyForm({ proxy, onDone }: ProxyFormProps) {
  const form = useProxyForm(proxy, onDone);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    form.submit();
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit} noValidate>
      <FormError message={form.save.isError ? describeError(form.save.error) : null} />
      <FormField
        label="Name"
        placeholder="VPN Amsterdam"
        value={form.name}
        error={form.errors.name}
        onChange={(event) => form.setName(event.target.value)}
      />
      <FormField
        label={proxy ? "New address" : "Address"}
        placeholder={proxy ? proxy.url : "socks5://gluetun-1:1080"}
        hint={proxy ? "Leave it empty to keep the current address." : ADDRESS_HINT}
        inputMode="url"
        spellCheck={false}
        autoCapitalize="off"
        autoComplete="off"
        value={form.url}
        error={form.errors.url}
        onChange={(event) => form.setUrl(event.target.value)}
      />
      <div className="flex flex-wrap gap-2">
        <Button type="submit" className="h-10" disabled={form.save.isPending}>
          {proxy ? "Save proxy" : "Add proxy"}
        </Button>
        {proxy && (
          <Button type="button" variant="ghost" className="h-10" onClick={onDone}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}
