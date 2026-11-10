# Presets

A preset is a named set of download options: quality, file names, any yt-dlp
option, plus yt-dlp-z settings such as cookies, proxy mode and media-server
layout. Downloads and subscriptions pick a preset instead of repeating options.

Create them on the **Presets** page. Changing a preset affects downloads started
afterwards; downloads already running keep the options they started with.

## Kinds of presets

Each preset has a **Use for** setting:

| Kind                       | Offered for                              |
| -------------------------- | ---------------------------------------- |
| **Any link**               | Everything                               |
| **Videos**                 | Single videos                            |
| **Playlists and channels** | Playlist and channel links               |
| **Live streams**           | Live and upcoming streams, and premieres |

Each kind can have one **default** preset. After the [link check](downloads.md#link-check)
the download form picks the default for that kind of link, or the default for
"any link" when there isn't one. For example: "Best quality" as the default for
videos, "Audio only" for playlists, and "Live streams" for live streams.

## What a preset holds

- **Name**
- **Common options**: quality, file name template, subtitles, thumbnail and
  metadata, SponsorBlock (see [Downloads](downloads.md#common-options))
- **Every other yt-dlp option** and extra command-line flags
- **Download folder**: overrides the default folder for this preset
- **Cookies**: a [cookies file](cookies.md) to sign in with
- **Proxy**: Off, next proxy in turn, random proxy, or same proxy per channel
  ([Proxies](proxies.md))
- **Live chat**: save a finished stream's chat, and maybe a scrolling overlay made from it
  ([Live chat](live-chat.md))
- **Sub-folders, file name, folder per video, media-server files**: a folder per
  channel (with or without season folders), each video in a folder of its own, names like `[20261103] Title` or
  `Channel - S2026E1103 - Title`, thumbnails and `.nfo` files
  ([Folders and media servers](media-server.md))

<a id="live-stream-presets"></a>

## Recording settings

Presets for live streams and for any link also hold the recording settings, used
whenever the link turns out to be a stream:

| Setting                                                    | Default  | Meaning                                                       |
| ---------------------------------------------------------- | -------- | ------------------------------------------------------------- |
| **New file every (hours)**                                 | 6        | Splits long streams into parts. Empty: one file per stream    |
| **Stop after (hours)**                                     | empty    | Counts hours of the stream. Empty: record until it ends       |
| **Record from the start, unless live longer than (hours)** | 6        | Empty: always from the start (up to 5 days of a 24/7 stream)  |
| **Streams live longer than that when found**               | from now | **Record from now**, or **Record their first N hours**        |
| **Download the VOD afterwards (hours after the stream)**   | empty    | Downloads YouTube's processed copy later. Empty: no VOD       |
| **Delete the recording once the VOD is saved**             | off      | Replaces the recording with the VOD if the VOD download works |

[Live recording](live-recording.md) explains each one.

A subscription can use a separate **Preset for live streams**. By default its streams
use the subscription's own preset, with that preset's recording settings if it has
them, else those of the default live-stream preset, else the default any-link preset.

## Deleting a preset

Downloads already queued or finished stay. Subscriptions using it need another
preset. Deleting a cookies file instead makes presets using it download without
cookies.
