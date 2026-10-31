import { SelectField } from "@/components/form-field";
import type { ProxyMode } from "@/lib/download-options";

const CHOICES: { value: ProxyMode; label: string }[] = [
  { value: "off", label: "Off: connect directly" },
  { value: "rotate", label: "Next proxy in turn" },
  { value: "random", label: "Random proxy" },
  { value: "sticky", label: "Same proxy per channel" },
];

interface ProxyFieldProps {
  value: ProxyMode;
  onChange: (value: ProxyMode) => void;
  /** Proxies in Settings → Proxies. With none, the field only shows to turn it off. */
  proxyCount: number;
}

/** Sends downloads through the proxy pool (backend services/proxies). */
export function ProxyField({ value, onChange, proxyCount }: ProxyFieldProps) {
  if (proxyCount === 0 && value === "off") {
    return null;
  }
  const hint =
    proxyCount === 0
      ? "There are no proxies in Settings → Proxies, so these downloads will fail."
      : "Each download keeps its proxy until it ends. Blocked proxies are skipped for 30 minutes.";
  return (
    <SelectField
      label="Proxy"
      hint={hint}
      value={value}
      choices={CHOICES}
      onValueChange={(choice) => onChange(choice as ProxyMode)}
    />
  );
}
