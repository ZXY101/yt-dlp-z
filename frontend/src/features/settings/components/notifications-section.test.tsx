import { screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

async function openSection() {
  const result = renderApp("/settings");
  const section = await screen.findByRole("region", { name: "Notifications" });
  await within(section).findByLabelText("Topic");
  return { ...result, section: within(section) };
}

describe("NotificationsSection", () => {
  it("saves the topic, token and chosen events", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user, section } = await openSection();

    await user.type(section.getByLabelText("Topic"), "my-downloads");
    await user.type(section.getByLabelText("Access token"), "tk_secret");
    await user.click(section.getByLabelText("Finished"));
    await user.click(section.getByRole("button", { name: "Save notifications" }));

    expect(await section.findByText("Notification settings saved.")).toBeInTheDocument();
    expect(server.notifications.topic).toBe("my-downloads");
    expect(server.notifications.events).toEqual([
      "recording_started",
      "download_failed",
      "problems",
    ]);
    expect(server.notificationToken).toBe("tk_secret");
    expect(section.getByLabelText("Access token")).toHaveValue("");
    expect(section.getByText("A token is saved. Type a new one to replace it.")).toBeVisible();
  });

  it("keeps the saved token unless it is removed", async () => {
    const server = createFakeServer();
    server.notifications = { ...server.notifications, topic: "dl", has_token: true };
    server.notificationToken = "tk_old";
    installFakeApi(server);
    const { user, section } = await openSection();

    await user.click(section.getByRole("button", { name: "Save notifications" }));
    await section.findByText("Notification settings saved.");
    expect(server.notificationToken).toBe("tk_old");

    await user.click(section.getByLabelText("Remove the saved token"));
    expect(section.getByLabelText("Access token")).toBeDisabled();
    await user.click(section.getByRole("button", { name: "Save notifications" }));
    await section.findByText("Optional.");
    expect(server.notificationToken).toBe("");
  });

  it("rejects topics ntfy wouldn't accept", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user, section } = await openSection();

    await user.type(section.getByLabelText("Topic"), "has spaces");
    await user.click(section.getByRole("button", { name: "Send test message" }));

    expect(section.getByText("Use up to 64 letters, digits, - and _ (no spaces).")).toBeVisible();
    expect(server.sentTests).toEqual([]);
  });

  it("sends a test message with the unsaved settings", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user, section } = await openSection();

    await user.type(section.getByLabelText("Topic"), "try-me");
    await user.click(section.getByRole("button", { name: "Send test message" }));

    expect(await section.findByText("Test message sent. Check your phone.")).toBeInTheDocument();
    expect(server.sentTests[0]?.topic).toBe("try-me");
    expect(server.notifications.topic).toBe("");
  });

  it("explains a test message that couldn't be sent", async () => {
    const server = createFakeServer();
    server.testError = "The ntfy server refused the access token.";
    installFakeApi(server);
    const { user, section } = await openSection();

    await user.type(section.getByLabelText("Topic"), "dl");
    await user.click(section.getByRole("button", { name: "Send test message" }));

    expect(
      await section.findByText("The ntfy server refused the access token."),
    ).toBeInTheDocument();
  });
});
