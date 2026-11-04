# Downloads

The **Download** page (the home page) downloads anything yt-dlp supports: a
video, a playlist, a whole channel, or a live stream. Everything you start shows
up on the **Queue** page.

## The download form

| Field                    | What it does                                                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| **Link**                 | A video, playlist or channel from [any site yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **Preset**               | Fills in the options below. You can still change them for this download                                                      |
| **Save to**              | Empty: the default folder. A relative path (`music/albums`) makes a sub-folder in it                                         |
| **Cookies**              | Overrides the preset's cookies file, for members-only or age-restricted videos                                               |
| **Proxy**                | Overrides the preset's [proxy mode](proxies.md) for this download                                                            |
| **Live chat**            | Saves a finished stream's chat, and can make a scrolling overlay from it ([details](live-chat.md))                           |
| **Media server**         | Saves the download as episodes for Jellyfin, Plex or Kodi ([details](media-server.md))                                       |
| **Common options**       | Quality, file name template, subtitles, thumbnail and metadata, SponsorBlock                                                 |
| **Advanced options**     | Every other yt-dlp option                                                                                                    |
| **Extra yt-dlp options** | Raw command-line flags, e.g. `--limit-rate 2M --embed-chapters`                                                              |

"Save to" suggests folders that already exist. Absolute paths are allowed only
inside the default folder or an extra download root (see
[Configuration](configuration.md#download-folders)).

### Link check

When you paste a link, yt-dlp-z asks yt-dlp what it is (usually in a couple of
seconds) and shows a preview: title, channel, thumbnail and what kind of link
it is:

- **Video**: downloads that one video.
- **Playlist**: warns that every video in it will be downloaded.
- **Channel**: warns that every video, Short and stream on all its tabs will be
  downloaded.
- **Live now**: offers to record it (see below).
- **Upcoming stream**: offers to schedule a recording for when it starts.

The preset picker switches to your default preset for that kind of link (see
[Presets](presets.md#kinds-of-presets)). If yt-dlp can't open the link
(private, removed, region-blocked), the error shows before you start.

### Playlist links

A link like `youtube.com/watch?v=…&list=…` points at a video _and_ a playlist.
yt-dlp-z asks which one you mean: **Just this video** or **The whole
playlist**. It never downloads the playlist without asking.

### Recording live streams

For a live or upcoming stream the form asks how to record it:

- **From the start**: fetches the stream from its first second, even if it
  has been live for a while.
- **From now**: starts at the live edge.
- **New file every (hours)** and **Stop after (hours)**, prefilled from your
  live-stream preset.

An upcoming stream becomes a **scheduled** recording that waits for the stream
to start. More in [Live recording](live-recording.md).

## Options

### Common options

| Option                           | Effect                                                                                                                            |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Quality**                      | Best available, up to 1080p, up to 720p, audio only, audio only (MP3), or custom                                                  |
| **File name template**           | yt-dlp's [output template](https://github.com/yt-dlp/yt-dlp#output-template), e.g. `%(title)s [%(id)s].%(ext)s`. Must be relative |
| **Embed subtitles**              | Downloads subtitles and puts them inside the video file                                                                           |
| **Embed thumbnail and metadata** | Title, uploader, date and cover art inside the file                                                                               |
| **Remove sponsor segments**      | Cuts sponsored sections using [SponsorBlock](https://sponsor.ajay.app)                                                            |

"Custom" quality means the format is set in Advanced options (`--format`).

### Advanced options

**Advanced options** opens every yt-dlp option, grouped like `yt-dlp --help`
(Network, Video selection, Download, Filesystem, Post-processing and so on) and
searchable by name, flag or help text (try "subtitles" or `--limit-rate`).

The list comes from the yt-dlp that's installed, so it always matches its
version, including options added by an [in-app update](ytdlp.md). Options are
stored by name, so presets keep working when yt-dlp changes.

A few options are managed by yt-dlp-z or blocked for safety; see
[blocked options](ytdlp.md#blocked-options).

### Extra yt-dlp options

A text box for anything else, written as on the command line. It's split like a
shell would split it (quotes work), but never run through a shell. The same
blocked options apply.

## The queue

The **Queue** page has three sections:

- **In progress**: running downloads and recordings with live progress (speed,
  size, time left; for recordings, the length recorded so far). Waiting jobs say
  "Waiting for a free download slot…" or "…recording slot…".
- **Scheduled**: recordings waiting for a stream to start.
- **Finished**: completed, failed and cancelled jobs.

How many run at once is set in **Settings**: **Downloads at the same time**
(default 3) and **Recordings at the same time** (default 2). Recordings have
their own slots, so a long queue of videos never delays a live stream.

### Actions

| Action     | What it does                                                                                              |
| ---------- | --------------------------------------------------------------------------------------------------------- |
| **Cancel** | Stops a running or queued job. A cancelled recording keeps what was recorded so far                       |
| **Retry**  | Runs a failed or cancelled job again with the same options                                                |
| **Log**    | yt-dlp's full output for that job                                                                         |
| **Keep**   | Pins a download so automatic cleanup never deletes it ([retention](subscriptions.md#delete-after-n-days)) |
| **Remove** | Removes the job from the list. Choose **keep files** or **delete files**                                  |

**Deleting files** removes the video and the files saved beside it with the
same name (`.nfo`, thumbnail, subtitles, other recording parts), only inside the
download's own folder. If the download came from a subscription, that video
won't be downloaded again.

If that was the channel's last video, its `tvshow.nfo` and artwork (`poster.jpg`,
`fanart.jpg`, `banner.jpg`) and the empty folder go too. Anything else in the
folder keeps them all in place.

### After a restart

Downloads that were running when the app stopped are marked as interrupted and
can be retried. Recordings of streams that are still live start again on their
own (see [Live recording](live-recording.md#restarts)).
