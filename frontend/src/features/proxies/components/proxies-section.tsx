import { TriangleAlert } from "lucide-react";

import { describeError } from "@/api/errors";
import { CheckboxField } from "@/components/checkbox-field";
import { Disclosure } from "@/components/disclosure";
import { FormError } from "@/components/form-error";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useProxies, useProxySettings, useSaveProxySettings } from "@/features/proxies/api";
import { ProxyCard } from "@/features/proxies/components/proxy-card";
import { ProxyForm } from "@/features/proxies/components/proxy-form";

function CookiesSetting() {
  const settings = useProxySettings();
  const save = useSaveProxySettings();
  if (!settings.data) {
    return null;
  }
  return (
    <>
      <FormError message={save.isError ? describeError(save.error) : null} />
      <CheckboxField
        label="Send downloads with cookies through proxies"
        description="Off: downloads that sign in with cookies connect directly. One account seen from many IP addresses can get flagged, and the cookies identify it anyway."
        checked={settings.data.send_cookies}
        disabled={save.isPending}
        onCheckedChange={(on) => save.mutate({ send_cookies: on })}
      />
    </>
  );
}

function VpnWarning() {
  return (
    <Alert>
      <TriangleAlert aria-hidden />
      <AlertDescription>
        YouTube often asks VPN and data-centre IP addresses to sign in. A proxy it blocks, or one
        that doesn&apos;t connect, is skipped for 30 minutes and the download moves on to the next.
      </AlertDescription>
    </Alert>
  );
}

/** The proxy pool: presets choose whether their downloads use it. */
export function ProxiesSection() {
  const proxies = useProxies();
  const list = proxies.data ?? [];
  return (
    <section className="space-y-4 border-t pt-6" aria-labelledby="proxies-heading">
      <div className="space-y-1">
        <h2 id="proxies-heading" className="text-lg font-medium">
          Proxies
        </h2>
        <p className="text-sm text-muted-foreground">
          HTTP or SOCKS proxies, such as one VPN container per server. Presets choose whether their
          downloads go through them.
        </p>
      </div>
      {proxies.isError && <FormError message={describeError(proxies.error)} />}
      {list.length > 0 && (
        <ul className="space-y-3" aria-label="Proxies">
          {list.map((proxy) => (
            <ProxyCard key={proxy.id} proxy={proxy} />
          ))}
        </ul>
      )}
      <Disclosure title="Add a proxy">
        <ProxyForm proxy={null} onDone={() => undefined} />
      </Disclosure>
      {list.length > 0 && <VpnWarning />}
      <CookiesSetting />
    </section>
  );
}
