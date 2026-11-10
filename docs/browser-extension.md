# Browser extension

The yt-dlp-z extension sends the page you're on, or a link you right-click, to your own
yt-dlp-z server. The server downloads or records it; nothing is downloaded in the browser.
It works in Chrome and other Chromium browsers (Edge, Brave, Vivaldi) and in Firefox,
including Firefox for Android.

It needs yt-dlp-z **0.1.6 or newer**. Older servers get a message saying so.

## Install

Store listings are on the way. Until then:

- **Chrome and other Chromium browsers:** download `yt-dlp-z-extension-<version>.zip` from
  the [releases page](https://github.com/ZXY101/yt-dlp-z/releases) and unzip it. Open
  `chrome://extensions`, switch on **Developer mode**, click **Load unpacked** and pick the
  unzipped folder.
- **Firefox:** open `about:debugging#/runtime/this-firefox`, click **Load Temporary
  Add-on** and pick `manifest.json` in the unzipped folder. Firefox removes temporary
  add-ons when it closes, until the signed version is on Firefox Add-ons.

To build it yourself, see [extension/README.md](../extension/README.md).

## Set up

The settings page opens when you install the extension (later: right-click the toolbar
button → Options).

1. In yt-dlp-z, open **Settings → API tokens**, make a token and choose **Send links only**.
   A send-only token can check links, list presets and start downloads, nothing else: it
   can't delete files, see the queue or change settings, so a stolen token can do little.
2. In the extension, enter the server's address (for example `http://192.168.1.5:9742`,
   a Tailscale name, or `https://yt.example.org`) and paste the token.
3. Click **Test and save**. The browser asks permission to talk to that one address. The
   extension checks the server's version and the token, and saves.

Plain HTTP is fine on your own network or Tailscale. Over the internet use HTTPS: the
extension warns when a token would travel over plain HTTP to a public address.

### Behind a login proxy

If yt-dlp-z sits behind a proxy with its own login (Authelia, Authentik, Cloudflare Access),
the proxy stops the extension's requests and **Test and save** says a login page answered.
Either:

- add a header your proxy accepts as a fixed credential under **Extra headers**, one
  `Name: value` per line (for example a Cloudflare Access service token:
  `CF-Access-Client-Id: …` and `CF-Access-Client-Secret: …`, or `Authorization: Basic …`),
  or
- let `/api/` through without the proxy's login and use a token. yt-dlp-z still checks the
  token on every request.

Servers running with `YTDLPZ_AUTH_MODE=none` don't need a token; leave the field empty.

## Use

**Toolbar button.** Click it on any page. It shows what the link is right away, then the
server's check fills in the details (2–7 s): title, thumbnail, length, how many videos, or
that a stream is live or upcoming. You don't have to wait for the check to click.

- Pick a preset, or keep **Default for this kind of link**. Your last choice is remembered.
- A video opened from a playlist offers **This video** or **Whole playlist**.
- The button says what will happen: **Download**, **Download 24 videos**, **Record** or
  **Schedule recording**.
- After sending, **Open queue** opens yt-dlp-z. The popup closes after two seconds, unless
  your pointer is on it. Closing it early doesn't cancel anything.

**Right-click menu** (desktop only):

- **Send to yt-dlp-z** on a link, a video or the page, with the default preset for that kind
  of link.
- **Send to yt-dlp-z with ▸** to pick a preset.
- **Send whole playlist to yt-dlp-z** on videos opened from a playlist.

The toolbar icon shows **…** while sending, then **✓** or **✗**, and a notification says
what happened. Whole playlists and channels are only sent from the toolbar button, which
shows how many videos they have first.

## Check links ahead (optional)

**Settings → Check links ahead on video pages** makes the toolbar button answer at once:
when you stay on a video page for about three seconds, the extension asks your server to
check it, and the popup later reads the answer from the server's cache.

It's off by default because it sends the address of every video page you stay on to your
server, and it needs permission to read the address of your tabs, which the browser asks
for when you switch it on. Only the active tab is checked, one page at a time, and pages
you leave within three seconds are skipped. Switching it off gives the permission back.

## Phones

| Browser                     | Works?                                                                                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Firefox for Android         | Yes: toolbar button (in the ⋮ menu → Extensions) and settings. No right-click menu, which Firefox for Android doesn't offer to extensions. |
| Chrome for Android          | No: Chrome on Android doesn't run extensions.                                                                                              |
| Safari / any browser on iOS | No: Safari only runs extensions packaged as an App Store app.                                                                              |

On Android you can also open yt-dlp-z in the browser and paste the link. A share-sheet
target (Share → yt-dlp-z) is planned.

## Permissions

| Permission                      | Why                                                          |
| ------------------------------- | ------------------------------------------------------------ |
| Access to your server's address | Asked at setup, for that one address only, to send it links. |
| Active tab                      | Read the page you're on when you click the toolbar button.   |
| Context menus                   | The right-click items.                                       |
| Notifications                   | Say whether a right-click send worked.                       |
| Storage                         | Keep the address, token and presets on this device.          |
| Tabs (optional)                 | Only for **Check links ahead**, asked when you switch it on. |

The extension has no content scripts, so it can't read or change the pages you visit.
See the [privacy policy](browser-extension-privacy.md).

## Troubleshooting

| Message                                          | What to do                                                                                                                                                                                                               |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Can't reach …                                    | Check the address and port, and that the server is up and reachable from this device (VPN, Tailscale).                                                                                                                   |
| Can't reach … in Firefox, by name over `http://` | HTTPS-Only Mode turns `http://` into `https://` for names (not for private IP addresses). Use the IP address, e.g. `http://192.168.1.5:9742`, or add an exception under Settings → Privacy & Security → HTTPS-Only Mode. |
| The server didn't accept the token               | The token was revoked or mistyped: make a new one in Settings → API tokens.                                                                                                                                              |
| This server needs an API token                   | Make a send-only token and paste it.                                                                                                                                                                                     |
| A login page answered instead of yt-dlp-z        | See [Behind a login proxy](#behind-a-login-proxy).                                                                                                                                                                       |
| This server runs yt-dlp-z 0.1.5                  | Update the server ([Installation → Updating](installation.md)).                                                                                                                                                          |
| Errors about the video itself                    | The same as on the download form: see [Troubleshooting](troubleshooting.md).                                                                                                                                             |
