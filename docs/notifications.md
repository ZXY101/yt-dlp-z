# Notifications

yt-dlp-z sends push notifications through [ntfy](https://ntfy.sh): the free
ntfy.sh service or your own ntfy server.

## Setup

1. Install the ntfy app ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy),
   [iOS](https://apps.apple.com/app/ntfy/id1625396347)) or use the web app.
2. In the app, subscribe to a topic with a name that's hard to guess, e.g.
   `ytdlpz-7f3k29xq`. Anyone who knows a topic on ntfy.sh can read it.
3. In yt-dlp-z, Settings → **Notifications**:
   - **Server**: `https://ntfy.sh` or your own server
   - **Topic**: the same topic. Empty turns notifications off
   - **Access token**: optional, for servers or topics that need login. Once
     saved it's never shown again; type a new one to replace it, or tick
     **Remove the saved token**
4. **Send test message** checks the values before you save them.

## Events

Each can be turned off.

| Event                 | When                                                                              |
| --------------------- | --------------------------------------------------------------------------------- |
| **Recording started** | A live stream began recording (once per recording)                                |
| **Finished**          | A download or recording finished                                                  |
| **Failed**            | A download or recording failed, with the error yt-dlp gave                        |
| **Problems**          | Cookies YouTube no longer accepts, or several failures in a row (once per streak) |

Sending happens in the background; if ntfy can't be reached, the failure is
only logged and downloads carry on.
