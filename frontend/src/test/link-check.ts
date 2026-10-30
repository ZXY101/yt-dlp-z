import { screen } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

// The form waits for typing to pause before checking the link.
export const CHECK_TIMEOUT = { timeout: 3000 };

/** Types a link into the download form and waits until its check has passed. */
export async function enterCheckedLink(user: UserEvent, url: string) {
  await user.type(await screen.findByLabelText("Link"), url);
  return screen.findByLabelText("Media details", {}, CHECK_TIMEOUT);
}
