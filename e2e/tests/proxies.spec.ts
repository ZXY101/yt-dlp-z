import type { Page } from "@playwright/test";

import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  signIn,
  test,
} from "../fixtures/app";

async function addProxy(page: Page, name: string, url: string) {
  const section = page.getByRole("region", { name: "Proxies" });
  const toggle = section.getByRole("button", { name: "Add a proxy" });
  if ((await toggle.getAttribute("aria-expanded")) !== "true") {
    await toggle.click();
  }
  await section.getByLabel("Name").last().fill(name);
  await section.getByLabel("Address").fill(url);
  await section.getByRole("button", { name: "Add proxy" }).click();
  await expect(section.getByText(name, { exact: true })).toBeVisible();
}

test.describe("proxies", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
    await page.goto("/settings");
  });

  test("downloads go through the pool and skip a blocked proxy", async ({ page }) => {
    const section = page.getByRole("region", { name: "Proxies" });
    await addProxy(page, "Blocked", "http://blocked:8888");
    await addProxy(page, "Good", "socks5://me:fake-secret@good:1080");
    await expect(section.getByText("socks5://me:****@good:1080")).toBeVisible();
    await expect(page.getByText("fake-secret")).toHaveCount(0);

    await section.getByRole("button", { name: "Test Good" }).click();
    await expect(section.getByText(/sites see 203\.0\.113\.7 \(ZZ\)/)).toBeVisible();
    await expectNoHorizontalScroll(page);

    await page.goto("/");
    await page.getByLabel("Link").fill("https://example.com/watch/hidden");
    await page.getByLabel("Proxy").selectOption("rotate");
    await page.getByRole("button", { name: "Download" }).click();
    await expect(page.getByText("Through proxy Good")).toBeVisible();
    await expect(page.getByText(/Saved to .*Fake video hidden/)).toBeVisible();
  });

  test("presets choose whether downloads use the pool", async ({ page }) => {
    await addProxy(page, "Good", "http://good:8888");
    await page.goto("/presets/new");
    await page.getByLabel("Name", { exact: true }).fill("Hidden");
    await page.getByLabel("Proxy").selectOption("sticky");
    await page.getByRole("button", { name: "Save preset" }).click();
    await expect(page.getByText(/through proxies/)).toBeVisible();
  });

  test("a proxy can be fixed, turned off and deleted", async ({ page }) => {
    const section = page.getByRole("region", { name: "Proxies" });
    await section.getByRole("button", { name: "Add a proxy" }).click();
    await section.getByLabel("Name").fill("Typo");
    await section.getByLabel("Address").fill("good:8888");
    await section.getByRole("button", { name: "Add proxy" }).click();
    await expect(section.getByText(/Enter scheme:\/\/host:port/)).toBeVisible();

    await section.getByLabel("Address").fill("http://dead:8888");
    await section.getByRole("button", { name: "Add proxy" }).click();
    await section.getByRole("button", { name: "Test Typo" }).click();
    await expect(section.getByText(/Test failed: Unable to connect to proxy/)).toBeVisible();

    await section.getByRole("button", { name: "Edit Typo" }).click();
    await section.getByLabel("New address").fill("http://good:8888");
    await section.getByRole("button", { name: "Save proxy" }).click();
    await expect(section.getByText("http://good:8888")).toBeVisible();
    await expect(section.getByText("Not tested yet")).toBeVisible();

    await section.getByRole("button", { name: "Turn off Typo" }).click();
    await expect(section.getByText("Turned off")).toBeVisible();

    await section.getByRole("button", { name: "Delete Typo" }).click();
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await expect(section.getByText("Typo", { exact: true })).toHaveCount(0);
  });

  test("downloads with cookies skip the pool unless allowed", async ({ page }) => {
    const setting = page.getByLabel("Send downloads with cookies through proxies");
    await setting.click();
    await expect(setting).toBeChecked();
    await page.reload();
    await expect(page.getByLabel("Send downloads with cookies through proxies")).toBeChecked();
  });
});
