import type { Proxy } from "@/features/proxies/types";

function time(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/** One line about whether the proxy can be used right now, and its last test. */
export function describeProxyStatus(proxy: Proxy, now = Date.now()) {
  if (!proxy.enabled) {
    return "Turned off";
  }
  if (proxy.cooldown_until && new Date(proxy.cooldown_until).getTime() > now) {
    return `Skipped until ${time(proxy.cooldown_until)}: blocked or not connecting`;
  }
  if (proxy.check_ok === true) {
    const ip = proxy.exit_ip ? `, sites see ${proxy.exit_ip}` : "";
    return `Worked at ${time(proxy.checked_at ?? "")}${ip}`;
  }
  if (proxy.check_ok === false) {
    return `Test failed: ${proxy.check_error ?? "no answer"}`;
  }
  return "Not tested yet";
}
