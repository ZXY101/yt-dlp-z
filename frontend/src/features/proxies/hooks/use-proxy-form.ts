import { useState } from "react";

import { useAddProxy, useUpdateProxy } from "@/features/proxies/api";
import type { Proxy } from "@/features/proxies/types";

interface FormErrors {
  name?: string;
  url?: string;
}

/** Adds a proxy, or edits one (`proxy`): an empty address keeps the saved one. */
export function useProxyForm(proxy: Proxy | null, onSaved: () => void) {
  const [name, setName] = useState(proxy?.name ?? "");
  const [url, setUrl] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const add = useAddProxy();
  const update = useUpdateProxy();
  const save = proxy ? update : add;

  function validate(): FormErrors {
    return {
      name: name.trim() ? undefined : "Enter a name",
      url: proxy || url.trim() ? undefined : "Enter the proxy's address",
    };
  }

  function handleSaved() {
    setName(proxy ? name : "");
    setUrl("");
    onSaved();
  }

  function submit() {
    const found = validate();
    setErrors(found);
    if (found.name || found.url) {
      return;
    }
    const address = url.trim() || null;
    if (proxy) {
      const body = { id: proxy.id, name, url: address, enabled: proxy.enabled };
      update.mutate(body, { onSuccess: handleSaved });
    } else {
      add.mutate({ name, url: address ?? "", enabled: true }, { onSuccess: handleSaved });
    }
  }

  return { name, setName, url, setUrl, errors, save, submit };
}
