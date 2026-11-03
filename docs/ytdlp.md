# yt-dlp and PO tokens

yt-dlp-z runs [yt-dlp](https://github.com/yt-dlp/yt-dlp) for every download.
This page covers keeping it working: updates, PO tokens, and which yt-dlp
options are managed by yt-dlp-z.

## Updating yt-dlp

YouTube changes often break older yt-dlp versions, so yt-dlp needs updating more
often than yt-dlp-z. Settings → **yt-dlp** shows the version in use and:

- **Update now** installs the newest `yt-dlp[default]` from PyPI.
- **Update channel**: **Stable** (releases) or **Nightly** (pre-releases with the
  newest fixes).
- **Check for updates** / the daily check: a minute after start and then once a
  day, the app checks for a newer version and shows "X is available".
- **Update automatically** (off by default) installs it then. It's off because
  an update changes what every later download runs.
- **Use bundled version** goes back to the yt-dlp that came with yt-dlp-z.

How it works: the update is pip-installed into `<config>/ytdlp`, which comes
first on `PYTHONPATH` for every yt-dlp run. So it survives container rebuilds
and app updates. The install goes to a staging folder first, so a failed update
never breaks the version in use. Downloads already running keep the version they
started with. Updating needs internet access to PyPI.

After an update, the options editor reloads its list from the new version.

## PO tokens

YouTube asks some clients for a "proof of origin" (PO) token before it serves
their formats. Without one, yt-dlp skips those formats or gets HTTP 403 errors,
and recordings can fail. The
[bgutil provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider)
makes tokens. Run it next to yt-dlp-z:

```yaml
services:
  bgutil-provider:
    image: brainicism/bgutil-ytdlp-pot-provider
    restart: unless-stopped
    # No ports needed when it shares a Docker network with yt-dlp-z.
```

Then set Settings → **PO tokens** → **Provider address** to
`http://bgutil-provider:4416` (without Docker: `http://127.0.0.1:4416`) and save.

Saving pings the provider and pip-installs the bgutil yt-dlp plugin of the
**same version** into `<config>/plugins` (needs PyPI access). Every yt-dlp run
then gets `--plugin-dirs <config>/plugins` and
`--extractor-args youtubepot-bgutilhttp:base_url=…`.

- The app checks the provider again at start and every 6 hours, and installs the
  matching plugin when the provider was updated.
- If the provider can't be reached then, Settings shows the error and yt-dlp
  keeps asking it (yt-dlp works without tokens, with fewer formats).
- Empty the address to turn PO tokens off and remove the plugin.
- The plugin isn't part of the image: installed globally, yt-dlp would load it
  on every run and warn about an unreachable server whenever no provider is set up.
- The plugin passes a job's proxy to the provider, so the provider must reach
  your [proxies](proxies.md) by the same addresses.

## Blocked options

Every yt-dlp option is available, except these.

**Always blocked**, because yt-dlp-z manages them itself: `--paths`,
`--cookies`, `--cookies-from-browser`, `--download-archive`, `--update`,
`--update-to`, `--batch-file`.

**Blocked unless `YTDLPZ_ALLOW_UNSAFE_OPTIONS=true`**, because they can run
programs or read and write files outside the download folder: `--exec`,
`--netrc-cmd`, `--plugin-dirs`, `--ffmpeg-location`, `--downloader`,
`--js-runtimes`, `--postprocessor-args`, `--downloader-args`,
`--load-info-json`, `--netrc-location`, `--config-locations`,
`--print-to-file`, `--cache-dir`, `--enable-file-urls`, `--alias`.

yt-dlp-z also ignores yt-dlp config files on the server (`--ignore-config`), so
every download uses exactly the options chosen in the app. File name templates
(`--output`) must be relative to the download folder.
