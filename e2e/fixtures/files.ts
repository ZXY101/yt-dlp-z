/** A fake Netscape cookies.txt: two cookies, obviously not real. */
export const FAKE_COOKIES = {
  name: "cookies.txt",
  mimeType: "text/plain",
  buffer: Buffer.from(
    [
      "# Netscape HTTP Cookie File",
      ".example.com\tTRUE\t/\tTRUE\t0\tSID\tfake-e2e-session",
      ".example.org\tTRUE\t/\tFALSE\t0\tPREF\tfake-e2e-pref",
    ].join("\n"),
  ),
};

export const NOT_COOKIES = {
  name: "notes.txt",
  mimeType: "text/plain",
  buffer: Buffer.from("SID=fake-e2e-session; path=/"),
};
