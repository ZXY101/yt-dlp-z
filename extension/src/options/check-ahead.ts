import { ext } from "../lib/browser.ts";
import { byId } from "../lib/dom.ts";
import {
  checkAheadRequest,
  loadCheckAhead,
  type Permissions,
  saveCheckAhead,
} from "../lib/settings.ts";

const toggle = byId<HTMLInputElement>("check-ahead");

async function handleChange(wanted: Permissions): Promise<void> {
  if (!toggle.checked) {
    await saveCheckAhead(false);
    await ext.permissions.remove(wanted);
    return;
  }
  // Called before any other await, so the browser still counts the click as the user's
  // action and shows its prompt (tabs and, on Firefox, sending browsing activity).
  const granted = await ext.permissions.request(wanted);
  toggle.checked = granted;
  await saveCheckAhead(granted);
}

export async function setUpCheckAhead(): Promise<void> {
  // Worked out up front: an await before permissions.request() would lose the user's click.
  const wanted = await checkAheadRequest();
  const [enabled, granted] = await Promise.all([
    loadCheckAhead(),
    ext.permissions.contains(wanted),
  ]);
  toggle.checked = enabled && granted;
  toggle.addEventListener("change", () => {
    handleChange(wanted).catch(console.error);
  });
}
