import {
  type APIRequestContext,
  type BrowserContext,
  type Page,
  chromium,
  expect,
} from "@playwright/test";
import { execFileSync } from "node:child_process";
import { cpSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { ADMIN_PASSWORD, completeSetupViaApi, test as appTest } from "./app";

const E2E_DIR = resolve(import.meta.dirname, "..");
const REPO_DIR = resolve(E2E_DIR, "..");

/** Builds the extension and copies it with its optional permissions granted up front. */
function prepareExtension(): string {
  execFileSync("npm", ["run", "build", "-w", "extension"], { cwd: REPO_DIR, stdio: "ignore" });
  const target = join(E2E_DIR, ".state", "extension");
  rmSync(target, { recursive: true, force: true });
  cpSync(join(REPO_DIR, "extension", "dist"), target, { recursive: true });
  // The browser's permission prompt can't be clicked in a test; granted permissions skip it.
  const manifestPath = join(target, "manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  manifest.host_permissions = ["http://127.0.0.1/*"];
  manifest.permissions.push("tabs");
  writeFileSync(manifestPath, JSON.stringify(manifest));
  return target;
}

let preparedPath: string | undefined;

export interface Extension {
  context: BrowserContext;
  id: string;
}

/** The options page, which the extension opens itself on install. */
export async function optionsPage(extension: Extension): Promise<Page> {
  const url = `chrome-extension://${extension.id}/options.html`;
  const open = extension.context.pages().find((page) => page.url() === url);
  if (open) return open;
  const page = await extension.context.newPage();
  await page.goto(url);
  return page;
}

/** Opens the popup as a page, as if the toolbar button was clicked on a tab showing `tabUrl`. */
export async function openPopup(extension: Extension, tabUrl: string): Promise<Page> {
  const page = await extension.context.newPage();
  await page.addInitScript((url) => {
    // A popup opened as a page is its own active tab; pretend the user's page is.
    const fakeTab = { id: 1, url, title: "Tab title", favIconUrl: "" };
    const api = (globalThis as unknown as { chrome: { tabs: { query: unknown } } }).chrome;
    api.tabs.query = async () => [fakeTab];
  }, tabUrl);
  await page.goto(`chrome-extension://${extension.id}/popup.html`);
  return page;
}

/** Signs `request` in as the admin and makes a send-only API token. */
export async function makeSendToken(request: APIRequestContext): Promise<string> {
  await completeSetupViaApi(request);
  await request.post("/api/auth/login", { data: { password: ADMIN_PASSWORD } });
  const response = await request.post("/api/tokens", { data: { name: "ext", scope: "send" } });
  expect(response.status()).toBe(201);
  return (await response.json()).token;
}

export async function connect(extension: Extension, address: string, token: string) {
  const page = await optionsPage(extension);
  await page.getByLabel("Server address").fill(address);
  await page.getByLabel("API token").fill(token);
  await page.getByRole("button", { name: "Test and save" }).click();
  await expect(page.getByText(/The token works/)).toBeVisible();
  return page;
}

export const test = appTest.extend<{ extension: Extension }>({
  extension: async ({ request: _request }, run) => {
    preparedPath ??= prepareExtension();
    const context = await chromium.launchPersistentContext("", {
      channel: "chromium",
      args: [`--disable-extensions-except=${preparedPath}`, `--load-extension=${preparedPath}`],
    });
    const worker = context.serviceWorkers()[0] ?? (await context.waitForEvent("serviceworker"));
    await run({ context, id: new URL(worker.url()).host });
    await context.close();
  },
});

export { expect };
