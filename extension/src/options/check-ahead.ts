import { ext } from "../lib/browser.ts";
import { byId } from "../lib/dom.ts";
import { loadCheckAhead, saveCheckAhead, TABS_PERMISSION } from "../lib/settings.ts";

const toggle = byId<HTMLInputElement>("check-ahead");

async function handleChange(): Promise<void> {
  if (!toggle.checked) {
    await saveCheckAhead(false);
    await ext.permissions.remove(TABS_PERMISSION);
    return;
  }
  // The browser asks the user; the change event still counts as their action.
  const granted = await ext.permissions.request(TABS_PERMISSION);
  toggle.checked = granted;
  await saveCheckAhead(granted);
}

export async function setUpCheckAhead(): Promise<void> {
  const [wanted, granted] = await Promise.all([
    loadCheckAhead(),
    ext.permissions.contains(TABS_PERMISSION),
  ]);
  toggle.checked = wanted && granted;
  toggle.addEventListener("change", () => {
    handleChange().catch(console.error);
  });
}
