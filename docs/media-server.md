# Media servers (Jellyfin, Plex, Kodi)

yt-dlp-z can save downloads the way media servers expect TV shows: one folder
per channel, videos as episodes, with thumbnails and `.nfo` metadata. Turn it on
per [preset](presets.md) or per download with the **Media server** setting.

## Layouts

**Season folders** (`season`):

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

**Flat** (`flat`): the same, without the `Season YYYY` folder.

- The season is the upload year; the episode number is the upload date
  (`MMDD`), so episodes sort by date.
- The media-server layout replaces the preset's file name template.
- yt-dlp-z adds `--write-thumbnail --convert-thumbnails jpg --embed-metadata`.

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
