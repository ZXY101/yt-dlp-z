# Aligning recordings

`/api/align` finds how far apart two to four recordings of the same event
are, from their audio. A typical case is a collab where every streamer
recorded their own stream: the streams started at different times, but they
share the same voices and game sound. A client (a sync add-on, a script) can
use the offsets to play the recordings in step.

It's an API only; there is nothing for it in the web UI.

## How it works

1. yt-dlp downloads the smallest audio-only format of each link over plain
   HTTPS (about 50 kbit/s, roughly 110 MB for 5 hours). Cookies work as for
   downloads. The links are fetched at the same time.
2. The download goes straight into ffmpeg, which turns it into 2 kHz mono as
   it arrives, so the downloaded file never touches disk. Only the 2 kHz audio
   is kept, in `<config>/align/`, outside your download folders.
3. The server compares loudness over time across the whole overlap to find
   the offset, then checks it on twelve one-minute pieces spread over the
   overlap. The share of pieces that match is the confidence. Loudness is used
   rather than the waveform because each streamer's copy of the shared sound
   goes through different codecs and mixes.
4. The audio is deleted as soon as the job finishes or fails. Only the
   result stays, in memory, until you delete it or nobody has asked for it
   for an hour. A job still running that nobody has checked on for a minute
   is stopped and its audio deleted (the client went away).

Limits:

- Ended streams and videos only, up to 12 hours each. Live streams are
  refused; they would never finish downloading.
- One alignment runs at a time. Starting another meanwhile returns `409`.
- Recordings must overlap by at least a minute.
- Proxies from the [proxy pool](proxies.md) are not used.

Expect well under a minute for a pair of two-hour streams: about 20 s to
download and convert, and a second to compare. If YouTube refuses a link
(HTTP 403, which happens now and then), that link is tried once more.

## The API

Every route needs a browser session or a full-access [API token](mcp.md).

### Start: `POST /api/align`

```bash
curl -H "Authorization: Bearer $YTDLPZ_TOKEN" -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.youtube.com/watch?v=AAA", "https://www.youtube.com/watch?v=BBB"]}' \
  https://your-server/api/align
```

Body: `urls` (2 to 4 distinct links; the first is the reference) and an
optional `cookie_id` (see [Cookies](cookies.md)). Answers `202` with
`{"id": "…"}`.

### Status: `GET /api/align/{id}`

```json
{
  "id": "…",
  "state": "done",
  "progress": 1.0,
  "streams": [
    { "url": "https://www.youtube.com/watch?v=AAA", "stage": "ready", "downloaded": 1.0 },
    { "url": "https://www.youtube.com/watch?v=BBB", "stage": "ready", "downloaded": 1.0 }
  ],
  "offsets": {
    "https://www.youtube.com/watch?v=AAA": 0.0,
    "https://www.youtube.com/watch?v=BBB": 83.42
  },
  "confidence": {
    "https://www.youtube.com/watch?v=AAA": 1.0,
    "https://www.youtube.com/watch?v=BBB": 0.88
  },
  "error": null
}
```

- `state`: `downloading`, `analysing`, `done` or `failed` (then `error` says
  why).
- `progress`: 0 to 1 over the whole job.
- `streams`: each link's part, in the order sent: `stage` is `downloading`,
  `converting` (ffmpeg finishing the last of the audio after the download) or
  `ready`, and `downloaded` the download's progress (0 to 1).
  Show these so a long download doesn't look stuck.
- `offsets`: seconds by which each recording's content is later than the
  first's. Here something said 10 minutes into AAA is said 10:00 + 83.42 s
  into BBB. `null` means no reliable match: the recordings don't overlap, or
  their audio is too different.
- `confidence`: 0 to 1 per link. Offsets below 0.5 are reported as `null`.
  The offset is accurate to about a tenth of a second (the delay between
  streamers wanders by about that much), so fine-tune it on the client if you
  need more.

Poll every few seconds. A running job nobody asks about for a minute is
stopped, and a finished result nobody asks for during an hour is dropped, so a
client that disappears leaves nothing behind.

### Delete: `DELETE /api/align/{id}`

Stops the job if it's running, deletes its audio and forgets the result.
Answers `204`, or `404` if it's already gone. Clients should call it when
they're done with the result.
