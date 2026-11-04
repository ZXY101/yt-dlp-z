const CHROME_EXTENSION_URL =
  "https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc";
const FIREFOX_EXTENSION_URL = "https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/";

function ExternalLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="underline underline-offset-2">
      {children}
    </a>
  );
}

/** How to get a cookies file, closed by default so it stays out of the way once you know. */
export function CookieExportSteps() {
  return (
    <details className="rounded-xl border p-4 text-sm">
      <summary className="cursor-pointer font-medium">How to export YouTube cookies</summary>
      <div className="mt-3 space-y-3 text-muted-foreground">
        <p>This is easiest on a computer: most phone browsers can't run these extensions.</p>
        <ol className="list-decimal space-y-2 pl-5">
          <li>
            Install <ExternalLink href={CHROME_EXTENSION_URL}>Get cookies.txt LOCALLY</ExternalLink>{" "}
            (Chrome) or <ExternalLink href={FIREFOX_EXTENSION_URL}>cookies.txt</ExternalLink>{" "}
            (Firefox), and allow it to run in private windows in the browser's extension settings.
          </li>
          <li>Open a private or incognito window and sign in to YouTube.</li>
          <li>
            In that same tab, go to <code>https://www.youtube.com/robots.txt</code>. Keep it the
            only private tab open.
          </li>
          <li>
            Use the extension to export the cookies for <code>youtube.com</code>.
          </li>
          <li>
            Close the private window without signing out, and don't open that session again. YouTube
            replaces the cookies of open sessions, which would stop the file working.
          </li>
          <li>Upload the file below, then press Test on it.</li>
        </ol>
        <p>
          Consider a secondary Google account: downloading while signed in can get an account
          rate-limited or banned.
        </p>
        <p>
          The file signs in as you, so treat it like a password and delete your copy after
          uploading.
        </p>
      </div>
    </details>
  );
}
