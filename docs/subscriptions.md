# Subscriptions

The **Subscriptions** page watches YouTube channels and playlists. New uploads
download automatically with the subscription's preset, and live streams are
recorded. Other sites can be downloaded but not watched (yet).

## Adding a subscription

**Channel**: a channel link (`https://www.youtube.com/@name`,
`/channel/UC…`) or just `@name`. **Or a playlist link** (any link with
`list=`): videos added to the playlist are downloaded instead.

| Setting                           | Meaning                                                                                                          |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Preset**                        | Download options for new uploads                                                                                 |
| **Preset for live streams**       | Options and recording settings for streams and premieres. Default: see [Presets](presets.md#live-stream-presets) |
| **Cookies**                       | Overrides the preset's cookies. Needed for members-only videos                                                   |
| **Check every (minutes)**         | How often to look for new uploads. Default 10, at least 5                                                        |
| **Download recent uploads now**   | How many of the newest uploads to download right away. Older ones are skipped                                    |
| **Delete downloads after (days)** | Optional retention, see below                                                                                    |
| **Watch this channel**            | Turn off to pause checking without losing the settings                                                           |

### Filters

| Filter                                           | Meaning                                                                    |
| ------------------------------------------------ | -------------------------------------------------------------------------- |
| **Videos / Shorts / Live streams and premieres** | Which kinds of uploads to take. Shorts are vertical videos up to 3 minutes |
| **Title must match**                             | A regular expression, case-insensitive, e.g. `podcast\|episode`            |
| **Skip titles matching**                         | A regular expression, e.g. `trailer\|teaser`                               |
| **Longest (minutes)**                            | Skip anything longer                                                       |
| **Only uploads published on or after**           | A date                                                                     |
| **Include members-only videos**                  | Needs cookies from a channel member                                        |

## How checking works

Every few minutes (plus a small random delay, so channels don't all poll at
once) yt-dlp-z reads the channel's RSS feed. It's cheap and needs no API key.
For each upload it hasn't seen, it asks yt-dlp what it is (video, Short, live
stream, premiere), applies the filters and queues it.

- Each video is handled once. If yt-dlp can't open it, it is tried again on the
  next check while it's still in the feed.
- On the first check, only the newest "download recent uploads now" videos are
  downloaded; older ones are marked as seen.
- Upcoming streams and premieres become [scheduled recordings](live-recording.md).
- A slower sweep of the channel's **Streams** tab catches streams the feed missed.
- When YouTube's feed fails (they have outages), the channel's Videos tab is
  read with yt-dlp instead.

**Playlists** are listed with yt-dlp on every check (up to 1,000 videos), and
the videos added since the last check are downloaded. Playlists people make add
new videos at the end, so the last ones count as the newest for "download
recent uploads now"; a channel's "Uploads" playlist (`UU…`) is newest first.
Mixes (`RD…`) can't be watched.

### The channel limit

Settings → **Channels to watch** limits how many subscriptions you can have
(5 by default, paused ones included). Many channels polled from one IP address
make rate limits and bot checks from YouTube more likely. Raise it if you need
to, ideally together with [PO tokens](ytdlp.md#po-tokens) and longer check
intervals.

## What a subscription downloaded

Tap a subscription card to see everything it downloaded or recorded, and how
much disk space the files use.

**Edit** shows the channel's recent videos and what happened to each
(downloaded, skipped by a filter, failed…):

- **Don't download** skips a video for good, and stops its download or
  recording if one is running.
- **Allow again** looks at it again on the next check.

## Deleting files

**Remove** on a download asks whether to keep or delete its files. Deleting
removes the video and the files beside it with the same name (`.nfo`,
thumbnail, subtitles, other recording parts), only inside the download's own
folder, and the subscription won't download that video again.

## Delete after N days

Optional, per subscription, off by default. An hourly sweep deletes the
subscription's downloads that finished more than that many days ago, the same
way as deleting by hand (they won't come back). **Keep** on a download pins it
so it's never deleted.

## Removing a subscription

Removing a subscription stops watching. Files already downloaded stay on disk.
