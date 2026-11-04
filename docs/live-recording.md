# Live recording

yt-dlp-z records YouTube live streams and premieres, from the stream's first
second when possible. Recordings come from a [subscription](subscriptions.md)
or from pasting a live or upcoming link on the [Download](downloads.md#recording-live-streams)
page.

Under the hood each recording is a yt-dlp run with `--live-from-start` (or from
the live edge) and `--wait-for-video` for streams that haven't started.

## Scheduled streams

When a stream is announced (an "upcoming" stream or premiere), yt-dlp-z notes
its start time and shows it under **Scheduled** on the Queue page. A scheduled
recording holds no process or queue slot, and survives restarts. Five minutes
before the announced start, yt-dlp starts and waits for the stream. If the
stream starts late, yt-dlp keeps checking (every 30 seconds to 5 minutes)
until it opens.

Cancel a scheduled or waiting recording from the Queue page at any time.

## Recording slots

Recordings run in their own slots, separate from downloads (Settings →
**Recordings at the same time**, default 2). A recording that finds no free
slot waits in the queue. Raise the limit if channels you follow often stream at
the same time; every recording uses bandwidth and disk the whole time.

## Recording settings

These live on [live-stream presets](presets.md#live-stream-presets), and the
Download page lets you change the first two for one recording.

### New file every N hours

Long and 24/7 streams are split into parts: `Title.mp4`, then
`Title (part 2).mp4` and so on. Default: every 6 hours. Empty: one file per
stream. The first file only gets a number once a part 2 starts.

### Stop after N hours

Stops recording after that many hours of the stream. Empty: record until the
stream ends.

### Record from the start, unless live longer than N hours

Recording from the start of a stream that has been live for days means
downloading days of video. So when a stream is found already live for longer
than this (default 6 hours), yt-dlp-z does one of:

- **Record from now**: start at the live edge (default).
- **Record their first N hours**: record the first N hours from the start, then stop.

Empty: always record from the start (YouTube keeps up to about 5 days).

## VOD after the stream

**Download the VOD afterwards (hours after the stream)** is optional and off
by default. That many hours after a recording ends, yt-dlp-z downloads the
stream again as a normal video. Why:

- A recording can have gaps (an expired link, a restart). The VOD doesn't.
- YouTube takes time to process long streams, so waiting a few hours gives the
  full-quality version.

The VOD gets " (VOD)" added to its title, so it never overwrites the recording.

With **Delete the recording once the VOD is saved**, the recording is deleted
after the VOD finishes. If the VOD fails (members-only, not archived, removed),
the recording stays.

## Restarts

When yt-dlp-z stops (a container restart or update), running recordings are
told to finish their files first. That's why the Docker example sets
`stop_grace_period: 10m`: saving a long recording (merging and embedding the
thumbnail) can take minutes.

When it starts again, recordings that were interrupted start again by
themselves if the stream is still live. The new recording becomes the next
part.

## Expiring stream links

YouTube's stream links expire after a few hours, which ends a yt-dlp recording
with "Cannot find refreshed url". If the stream is still live, yt-dlp-z carries
on with a new recording as the next part, so a long stream doesn't stop after
about 5 hours.

## Titles

YouTube adds the date and time to live streams' titles
(`Stream title 2026-11-03 18:00`). yt-dlp-z strips it, so the file is named
after the stream itself.

## Members-only streams

Members-only streams need a member's cookies on the subscription or its preset.
See [Cookies](cookies.md).

## Tips

- Record to a fast local disk; copy elsewhere afterwards.
- Use [notifications](notifications.md) to hear when a recording starts or fails.
- For channels that stream 24/7, set **Stop after** or a short **New file every**.
- Turn on [PO tokens](ytdlp.md#po-tokens) if recordings fail with HTTP 403.

## Live chat

With the preset's [live chat](live-chat.md) setting on, a recording also saves the stream's chat
while it runs, and each part gets its own chat file and overlay when the recording ends. It starts with
the recording and follows YouTube's filtered Top chat, so a VOD, which fetches the whole unfiltered
replay, has more.
