# Cookies

Some videos only work when signed in: members-only videos and streams, private
or unlisted-with-login videos, age-restricted videos. yt-dlp signs in with a
**cookies file** exported from a browser where you're logged in.

## Adding a cookies file

1. In a browser, sign in to the site.
2. Export the cookies as a Netscape-format `cookies.txt` with an extension such
   as "Get cookies.txt LOCALLY" (Chrome) or "cookies.txt" (Firefox). Pick one
   that exports locally and doesn't upload your cookies anywhere.
3. On the **Cookies** page, upload the file and give it a name ("YouTube").
4. **Test** it: give a page that only works when signed in, such as a
   members-only video. The test tells you whether yt-dlp could open it.

Then pick the cookies file on a [preset](presets.md), a
[subscription](subscriptions.md) or a single download.

### YouTube: export from a private window

YouTube rotates the cookies of open browser sessions, which quietly
invalidates an exported file. To get a file that lasts:

1. Open a private / incognito window and sign in to YouTube there.
2. Open any video, then export the cookies for `youtube.com`.
3. Close the private window without signing out.

Consider a secondary Google account: downloading with an account can get it
rate-limited or flagged.

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
