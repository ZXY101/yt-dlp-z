# Privacy policy: yt-dlp-z browser extension

_Last updated: 2026-11-11_

The yt-dlp-z browser extension is a companion for a yt-dlp-z server that **you** run. It has
no servers of its own, no analytics and no tracking.

## What it stores

On your device, in the browser's extension storage (never synced to other devices):

- the address of your yt-dlp-z server,
- your API token and any extra headers you entered,
- your server's preset names, the last preset you picked, and whether "Check links ahead"
  is on.

Removing the extension deletes all of it.

## What it sends, and where

Only to the server address you entered:

- the address of the page or link when you click the toolbar button or a right-click item,
  so your server can check it and download or record it;
- with **Check links ahead** switched on (off by default): the address of each video page you
  stay on for about three seconds, so your server can check it ahead of time. Switching it on
  asks for your consent first (in Firefox, the browser's own "browsing activity" prompt), and
  switching it off withdraws it;
- your token and extra headers, with every request, so your server knows it's you.

Nothing is sent to the extension's authors or to any third party. The extension doesn't read
page contents: it has no content scripts.

What your server does with the links (downloading them, keeping logs) is up to how you run
it; see the yt-dlp-z documentation.

## Contact

Questions: open an issue at https://github.com/ZXY101/yt-dlp-z/issues.
