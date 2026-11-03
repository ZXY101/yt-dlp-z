# Folders, file names and media servers

yt-dlp-z can save downloads in a folder per channel, with the file names you
pick, and add the thumbnails and `.nfo` metadata media servers read. Three
settings, per [preset](presets.md) or per download, each independent of the
others:

| Setting                | Choices                                                                                                                             |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Sub-folders**        | none · `Channel/` · `Channel/Season 2026/`                                                                                          |
| **File name**          | yt-dlp default or your template · `Title [id]` · `[20261103] Title` · `[20261103] Title [id]` · `Channel - S2026E1103 - Title [id]` |
| **Media-server files** | off · thumbnail + `.nfo` per video, `tvshow.nfo` + artwork per channel                                                              |

A chosen file name replaces the file name template. With only a sub-folder
chosen, your template (or yt-dlp's default `Title [id]`) is used inside it.

**Dates are the day it aired**: a live stream's or premiere's start date, else
the upload date. (YouTube's upload date for a stream is when its waiting room was
made, often weeks earlier.)

## For a TV library

Pick `Channel/Season 2026/`, `Channel - S2026E1103 - Title [id]` and
media-server files:

```
Channel Name/
├── tvshow.nfo
├── poster.jpg
├── fanart.jpg
├── banner.jpg
└── Season 2026/
    ├── Channel Name - S2026E1031 - Video title [dQw4w9WgXcQ].mkv
    ├── Channel Name - S2026E1031 - Video title [dQw4w9WgXcQ].nfo
    └── Channel Name - S2026E1031 - Video title [dQw4w9WgXcQ].jpg
```

Or `Channel/` for the same without season folders.

- The season is the year it aired; the episode number is the date (`MMDD`), so
  episodes sort by date.
- Media-server files add
  `--write-thumbnail --convert-thumbnails jpg --embed-metadata`.

## For a plain archive

`Channel/` with `[20261103] Title` gives `Channel Name/[20261103] Video
title.mkv`, sorted by date in any file browser.

## Metadata files

- **Episode `.nfo`** next to every finished file (and every part of a
  recording): title, description, air date, channel (as studio), length,
  season and episode, and the video ID.
- **`tvshow.nfo`** in the channel folder, written once and never overwritten,
  so your edits stay.
- **Channel artwork**, fetched once by the first download into a channel folder
  without it: `poster.jpg` (the channel picture), `fanart.jpg` (the whole
  banner) and `banner.jpg` (the banner's widest strip). Existing files are never
  replaced.

## Setting up the library

Add the download folder (or the folder your preset saves to) as a **Shows** /
**TV** library:

- **Jellyfin**: library type "Shows". Under the library's metadata settings,
  keep "Nfo" as a metadata reader and move it to the top so the `.nfo` files win.
- **Plex**: library type "TV Shows" with a local-metadata agent (or the
  community "YouTube-Agent"); Plex doesn't read `.nfo` files by default.
- **Kodi**: content type "TV shows", scraper "Local information only".

Point live-stream presets at the same layout and recordings become episodes too.
