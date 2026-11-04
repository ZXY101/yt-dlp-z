# Cookies

Some videos only work when signed in: members-only videos and streams, private
or unlisted-with-login videos, age-restricted videos. yt-dlp signs in with a
**cookies file** exported from a browser where you're logged in.

## Adding a cookies file

The **Cookies** page has these steps too, under **How to export YouTube cookies**.

The export is easiest on a computer: most phone browsers can't run these extensions.

1. Install an extension that exports cookies locally and doesn't upload them
   anywhere: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   (Chrome) or [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
   (Firefox). If you have the older Chrome extension "Get cookies.txt" (no
   "LOCALLY"), uninstall it: it was reported as malware.
2. Allow the extension to run in private windows, in the browser's extension
   settings.
3. Export the cookies. For YouTube, follow the steps below. For other sites,
   sign in and export the cookies for that site.
4. On the **Cookies** page, upload the file and give it a name ("YouTube").
5. **Test** it: give a page that only works when signed in, such as a
   members-only video. The test tells you whether yt-dlp could open it.

Then pick the cookies file on a [preset](presets.md), a
[subscription](subscriptions.md) or a single download.

The file signs in as you, so treat it like a password and delete your copy after
uploading.

### Exporting YouTube cookies

YouTube rotates the cookies of open browser sessions as a security measure,
which quietly invalidates an exported file. To get a file that lasts, export from
a session that's never opened again
([yt-dlp's guide](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)):

1. Open a new private / incognito window and sign in to YouTube.
2. In the same tab, go to `https://www.youtube.com/robots.txt`. Keep it the only
   private tab open.
3. Export the cookies for `youtube.com` with the extension.
4. Close the private window without signing out, and don't open that session
   again.

Consider a secondary Google account: downloading while signed in can get an
account rate-limited or banned, temporarily or for good. Use cookies only for
videos that need them.

## How the file is used

- Stored in `<config>/cookies/`, readable only by yt-dlp-z's own user.
- Never sent back by the API or shown again; you can only replace or delete it.
- yt-dlp-z passes `--cookies` itself (you can't set it as an option). Each
  download gets its own temporary copy, because yt-dlp writes cookies back
  when it exits.
- Downloads with cookies skip the [proxy pool](proxies.md) unless you turn on
  **Send downloads with cookies through proxies**: one account seen from many
  IP addresses can get flagged.

## When cookies stop working

Errors such as "Sign in to confirm you're not a bot" or "This video is
available to this channel's members" on a download that has cookies mean the
file has expired. Export a new one, upload it, pick it on the presets and
subscriptions that used the old one, then delete the old file (names must be
unique, so upload the new one under another name first). [Notifications](notifications.md) can tell you when
this happens ("Problems").

Deleting a cookies file makes presets that used it download without cookies.
