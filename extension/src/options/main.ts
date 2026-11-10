import { normalizeAddress, originPattern } from "../lib/address.ts";
import { ext } from "../lib/browser.ts";
import { byId, element } from "../lib/dom.ts";
import { askRefreshPresets } from "../lib/messages.ts";
import { asServerProblem } from "../lib/problems.ts";
import { loadConnection, saveConnection, savePresets, type Connection } from "../lib/settings.ts";
import { setUpCheckAhead } from "./check-ahead.ts";
import { formatHeaders, parseHeaders } from "./headers.ts";
import { testConnection } from "./test-connection.ts";

const form = byId<HTMLFormElement>("connection");
const addressInput = byId<HTMLInputElement>("address");
const tokenInput = byId<HTMLInputElement>("token");
const headersInput = byId<HTMLTextAreaElement>("headers");
const saveButton = byId<HTMLButtonElement>("save");
const status = byId("status");
const results = byId<HTMLUListElement>("results");
const tokensLink = byId<HTMLAnchorElement>("tokens-link");

type Tone = "ok" | "warn" | "error";

function report(tone: Tone, text: string): void {
  results.append(element("li", tone, text));
}

function updateTokensLink(): void {
  try {
    tokensLink.href = `${normalizeAddress(addressInput.value)}/settings`;
  } catch {
    tokensLink.removeAttribute("href");
  }
}

function readForm(): Connection {
  return {
    address: normalizeAddress(addressInput.value),
    token: tokenInput.value.trim(),
    headers: parseHeaders(headersInput.value),
  };
}

async function testAndSave(connection: Connection): Promise<void> {
  const result = await testConnection(connection);
  report("ok", `Connected to yt-dlp-z ${result.version}.`);
  const count = result.presets.length;
  report("ok", `The token works. ${count} ${count === 1 ? "preset" : "presets"} found.`);
  for (const warning of result.warnings) report("warn", warning);
  await saveConnection(connection);
  addressInput.value = connection.address;
  await savePresets(result.presets);
  await askRefreshPresets();
  status.textContent = "Saved. Use the toolbar button or right-click a link.";
}

async function handleSubmit(event: SubmitEvent): Promise<void> {
  event.preventDefault();
  results.replaceChildren();
  status.textContent = "";
  let connection: Connection;
  try {
    connection = readForm();
  } catch (error) {
    report("error", error instanceof Error ? error.message : "Check the address.");
    return;
  }
  // Asked first, while the click still counts as a user action: browsers require one.
  const allowed = await ext.permissions.request({ origins: [originPattern(connection.address)] });
  if (!allowed) {
    report("error", "The extension needs permission to talk to this address.");
    return;
  }
  saveButton.disabled = true;
  status.textContent = "Testing…";
  try {
    await testAndSave(connection);
  } catch (error) {
    status.textContent = "";
    report("error", asServerProblem(error).message);
  } finally {
    saveButton.disabled = false;
  }
}

async function fillForm(): Promise<void> {
  const connection = await loadConnection();
  if (!connection) return;
  addressInput.value = connection.address;
  tokenInput.value = connection.token;
  headersInput.value = formatHeaders(connection.headers);
  byId<HTMLDetailsElement>("headers-section").open = connection.headers.length > 0;
  updateTokensLink();
}

form.addEventListener("submit", (event) => {
  handleSubmit(event).catch(console.error);
});
addressInput.addEventListener("input", updateTokensLink);
fillForm().catch(console.error);
setUpCheckAhead().catch(console.error);
