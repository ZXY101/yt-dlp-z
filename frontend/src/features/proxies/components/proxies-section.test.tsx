import { screen, within } from "@testing-library/react";

import { describeProxyStatus } from "@/features/proxies/components/proxy-status";
import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeProxy } from "@/test/fake-proxies";
import { renderApp } from "@/test/render";

async function openSection() {
  const result = renderApp("/settings");
  const section = await screen.findByRole("region", { name: "Proxies" });
  await within(section).findByLabelText("Send downloads with cookies through proxies");
  return { ...result, section: within(section) };
}

describe("ProxiesSection", () => {
  it("adds a proxy and never shows its password", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user, section } = await openSection();

    await user.click(section.getByRole("button", { name: "Add a proxy" }));
    await user.click(section.getByRole("button", { name: "Add proxy" }));
    expect(section.getByText("Enter a name")).toBeVisible();
    expect(section.getByText("Enter the proxy's address")).toBeVisible();

    await user.type(section.getByLabelText("Name"), "VPN 1");
    await user.type(section.getByLabelText("Address"), "socks5://me:hunter2@vpn-1:1080");
    await user.click(section.getByRole("button", { name: "Add proxy" }));

    const card = within(await section.findByRole("listitem"));
    expect(card.getByText("socks5://me:****@vpn-1:1080")).toBeVisible();
    expect(card.getByText("Not tested yet")).toBeVisible();
    expect(section.getByLabelText("Address")).toHaveValue("");
    expect(section.getByText(/YouTube often asks VPN/)).toBeVisible();
  });

  it("shows the server's error for a bad address", async () => {
    installFakeApi(createFakeServer());
    const { user, section } = await openSection();

    await user.click(section.getByRole("button", { name: "Add a proxy" }));
    await user.type(section.getByLabelText("Name"), "Bad");
    await user.type(section.getByLabelText("Address"), "vpn-1");
    await user.click(section.getByRole("button", { name: "Add proxy" }));
    expect(await section.findByText("Enter scheme://host:port")).toBeVisible();
  });

  it("tests, turns off, edits and deletes a proxy", async () => {
    const server = createFakeServer();
    server.proxies = [makeProxy(), makeProxy({ id: 2, name: "Dead", url: "http://dead:8888" })];
    installFakeApi(server);
    const { user, section } = await openSection();

    await user.click(await section.findByRole("button", { name: "Test VPN 1" }));
    expect(await section.findByText(/sites see 203\.0\.113\.7 \(ZZ\)/)).toBeVisible();
    await user.click(section.getByRole("button", { name: "Test Dead" }));
    expect(await section.findByText("Test failed: Unable to connect to proxy")).toBeVisible();

    await user.click(section.getByRole("button", { name: "Turn off VPN 1" }));
    expect(await section.findByText("Turned off")).toBeVisible();
    expect(server.proxies[0]?.enabled).toBe(false);
    await user.click(section.getByRole("button", { name: "Turn on VPN 1" }));
    await section.findByRole("button", { name: "Turn off VPN 1" });

    await user.click(section.getByRole("button", { name: "Edit VPN 1" }));
    const name = section.getByDisplayValue("VPN 1");
    await user.clear(name);
    await user.type(name, "Amsterdam");
    await user.click(section.getByRole("button", { name: "Save proxy" }));
    expect(await section.findByText("Amsterdam")).toBeVisible();
    expect(server.proxies[0]?.url).toBe("socks5://vpn-1:1080");

    await user.click(section.getByRole("button", { name: "Delete Dead" }));
    await user.click(await screen.findByRole("button", { name: "Delete" }));
    await screen.findByText("Amsterdam");
    expect(server.proxies.map((proxy) => proxy.name)).toEqual(["Amsterdam"]);
  });

  it("saves whether downloads with cookies use the pool", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user, section } = await openSection();

    await user.click(section.getByLabelText("Send downloads with cookies through proxies"));
    await vi.waitFor(() => expect(server.proxySettings.send_cookies).toBe(true));
  });
});

describe("describeProxyStatus", () => {
  it("puts a cooldown before the last test", () => {
    const now = Date.parse("2026-10-31T10:00:00Z");
    const cooling = makeProxy({ check_ok: true, cooldown_until: "2026-10-31T10:20:00+00:00" });
    expect(describeProxyStatus(cooling, now)).toMatch(
      /^Skipped until .+: blocked or not connecting$/,
    );
    const over = makeProxy({ cooldown_until: "2026-10-31T09:00:00+00:00" });
    expect(describeProxyStatus(over, now)).toBe("Not tested yet");
    const unknown = makeProxy({ check_ok: false });
    expect(describeProxyStatus(unknown, now)).toBe("Test failed: no answer");
  });
});
