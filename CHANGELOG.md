# Changelog

## 0.1.0 (2026-10-31)


### ⚠ BREAKING CHANGES

* the server now listens on 9742 by default (YTDLPZ_PORT still overrides it); the Docker image exposes 9742.

### Features

* allow setting the admin password with YTDLPZ_ADMIN_PASSWORD ([b9f2218](https://github.com/ZXY101/yt-dlp-z/commit/b9f2218a6de364d738fd6eb295a322a308c35ec3))
* **backend:** add download jobs with live progress and yt-dlp option schema ([758e5da](https://github.com/ZXY101/yt-dlp-z/commit/758e5da6418320d53798c649a169d72d3adde2b7))
* **backend:** add FastAPI server with first-run setup and login ([3542088](https://github.com/ZXY101/yt-dlp-z/commit/354208890a80837585951332d533ab4ef00890f4))
* **backend:** add openapi command that prints the API schema ([acb72e3](https://github.com/ZXY101/yt-dlp-z/commit/acb72e31912d3187b180fed6ff6aad9f8a5801ce))
* **backend:** add presets API ([96e638d](https://github.com/ZXY101/yt-dlp-z/commit/96e638d600e06690b9575bae9b874ac077e0e4f1))
* **backend:** change the download folder and download limit at runtime ([d8056c6](https://github.com/ZXY101/yt-dlp-z/commit/d8056c6b2454f281d352ae10811cbdee9a242f01))
* **backend:** check daily for a newer yt-dlp and optionally install it ([9fe7bff](https://github.com/ZXY101/yt-dlp-z/commit/9fe7bffc24616bf63a2297bf8c06bf883f3068fc))
* **backend:** check links before downloading and record streams on demand ([3bd8b40](https://github.com/ZXY101/yt-dlp-z/commit/3bd8b4073ce37f283d58e31e9a7ccc673cf76203))
* **backend:** record live and upcoming streams from subscriptions ([247791a](https://github.com/ZXY101/yt-dlp-z/commit/247791ae6293ee72252274c13dbfd225bdf45ade))
* **backend:** restart interrupted recordings after a restart ([328b9dc](https://github.com/ZXY101/yt-dlp-z/commit/328b9dc3f7f9a8e782ee2beb39274a7851b2b692))
* **backend:** split, limit and safely stop recordings ([2b4a84c](https://github.com/ZXY101/yt-dlp-z/commit/2b4a84c5cd72233e9ae2e1889f3664a740c093ef))
* **backend:** sweep the streams tab for streams the feed missed ([9b4b4d4](https://github.com/ZXY101/yt-dlp-z/commit/9b4b4d41272eee138c77ba5570678d828b261101))
* **backend:** update yt-dlp from the app ([02bad2b](https://github.com/ZXY101/yt-dlp-z/commit/02bad2b629a2532e1fe79d2e5a0d49f97ff07e8a))
* **backend:** upload cookies files and use them for downloads ([a208b6a](https://github.com/ZXY101/yt-dlp-z/commit/a208b6a307d5b4d37184b686235925ef934f72ae))
* **backend:** watch YouTube channels and queue their new uploads ([0cfed05](https://github.com/ZXY101/yt-dlp-z/commit/0cfed05b8a57b2535d26795e5809ef7f5b80f0bb))
* change the default port from 8080 to 9742 ([1190326](https://github.com/ZXY101/yt-dlp-z/commit/1190326dadc170684932e2b20a24a399eda6552d))
* **frontend:** add download form, live queue and setup warnings ([f4c6664](https://github.com/ZXY101/yt-dlp-z/commit/f4c6664c2551b13ec6cc306ae672ad099f758b01))
* **frontend:** add presets, cookies and settings pages and an options editor ([e16bffb](https://github.com/ZXY101/yt-dlp-z/commit/e16bffb7388525a9ab2a7fea75d170b89cd6aebf))
* **frontend:** add React app with first-run setup, login and app shell ([393c061](https://github.com/ZXY101/yt-dlp-z/commit/393c061d8b1003b4c2a0648cbc4ecb4723929708))
* **frontend:** add the Subscriptions page and the channel limit setting ([53438bb](https://github.com/ZXY101/yt-dlp-z/commit/53438bbbb50de0ae029aa240aff2d0d15785e414))
* **frontend:** ask before downloading a whole playlist ([14548f8](https://github.com/ZXY101/yt-dlp-z/commit/14548f84008531f3a69382f4fc9133dd340bcdd5))
* **frontend:** check links before downloading and record streams ([ab24622](https://github.com/ZXY101/yt-dlp-z/commit/ab246223d9cab2eccdd888f6d6e6729f508a5cf6))
* **frontend:** link the app name in the header to the download page ([cfe45f6](https://github.com/ZXY101/yt-dlp-z/commit/cfe45f6230aa77a83841cade9d4b81d318266d05))
* **frontend:** make Download the home page and drop the dashboard ([1dda7c4](https://github.com/ZXY101/yt-dlp-z/commit/1dda7c482176077076a6997ad4dcf4506364a699))
* **frontend:** make empty states clickable ([0b9c7df](https://github.com/ZXY101/yt-dlp-z/commit/0b9c7dfde16ce5945d6296ff897ab45af0424104))
* **frontend:** recording settings and parts in the queue ([f3e8910](https://github.com/ZXY101/yt-dlp-z/commit/f3e8910d39862532c7d11283d01f806dd7f2bda5))
* **frontend:** show all yt-dlp options in a dialog with group tabs ([d032dfe](https://github.com/ZXY101/yt-dlp-z/commit/d032dfe0d3edadab7b0ae98d2fc9aaeac09606d4))
* **frontend:** show available yt-dlp updates and an auto-update option ([738bbce](https://github.com/ZXY101/yt-dlp-z/commit/738bbcec996dd3c271a461cb4376922b9c48fb1d))
* **frontend:** show scheduled and running recordings ([218aed8](https://github.com/ZXY101/yt-dlp-z/commit/218aed8d57b717e41ade1e338fd650ec2761eafa))
* **frontend:** update yt-dlp from Settings ([ea6a542](https://github.com/ZXY101/yt-dlp-z/commit/ea6a542f4d36059cee5dac55ce73acff64cc8f78))
* media-server output per preset ([8a566ab](https://github.com/ZXY101/yt-dlp-z/commit/8a566ab1a52699913ff6f6c2a2cef46d5908ea9f))
* ntfy notifications ([7adb78a](https://github.com/ZXY101/yt-dlp-z/commit/7adb78a05fdf12d4ec249df56e1ef0898592f25a))
* presets per kind of link with recording settings ([6296612](https://github.com/ZXY101/yt-dlp-z/commit/62966124f340f8bb53ba5483a736dd7f2952a5ea))
* proxy pool ([c4b3a06](https://github.com/ZXY101/yt-dlp-z/commit/c4b3a06cc308201bb8dea526901cc86bf6eba0bb))
* record the first hours of streams found after running long ([9848d5a](https://github.com/ZXY101/yt-dlp-z/commit/9848d5a65e9f93263bdaf6df59ad8aff93d1b8e1))
* suggest existing folders in the "Save to" field ([489d2ff](https://github.com/ZXY101/yt-dlp-z/commit/489d2ff0ee14e233229fc542a18b9358ee94460c))


### Bug Fixes

* **backend:** don't let the link check pass unavailable videos ([74e1a06](https://github.com/ZXY101/yt-dlp-z/commit/74e1a06cbc1ba8f83912d15fcfb2fc9c08ee5c4b))
* **backend:** keep no copy when an update matches the bundled yt-dlp ([881e455](https://github.com/ZXY101/yt-dlp-z/commit/881e455ce947b3b6a6b6b8c9fcb1f487dc253fb0))
* **backend:** read upcoming streams instead of failing on them ([388fd82](https://github.com/ZXY101/yt-dlp-z/commit/388fd82976c8e1ed6eb44cb31daeeb23cc7e26b5))
* **backend:** show progress of recordings ([06311d4](https://github.com/ZXY101/yt-dlp-z/commit/06311d4daa9b63d88681afc3d2527c808f9a2b7b))
* **backend:** show progress of recordings joined mid-stream ([ff62e83](https://github.com/ZXY101/yt-dlp-z/commit/ff62e83b64d80c17e5478e61ed0b78f9981b7b55))
* **backend:** start every new job with an empty log ([0b181a7](https://github.com/ZXY101/yt-dlp-z/commit/0b181a720f51746d432b717ff3be7ec6de5144e1))
* **backend:** stop the yt-dlp options reader when the app shuts down ([d5620fc](https://github.com/ZXY101/yt-dlp-z/commit/d5620fce321f50f1fba846f3b6ffbc1b5e5f0934))
* **frontend:** center checkbox rows that have no description ([fee70d8](https://github.com/ZXY101/yt-dlp-z/commit/fee70d8c45612e8ec70946542ad32d4222db6dfc))
* **frontend:** give the queue the same width as other pages ([f71d69e](https://github.com/ZXY101/yt-dlp-z/commit/f71d69ecd9f0aedad94ef998a6a89e2a05e65fe8))
* **frontend:** line checkbox labels up with the box ([bd7ddff](https://github.com/ZXY101/yt-dlp-z/commit/bd7ddffd222ddd882660ccd7fbbb878940a2de2d))
* **frontend:** make dropdown options readable in dark mode ([cae807d](https://github.com/ZXY101/yt-dlp-z/commit/cae807d8b13f2124acff52b2fd5e01486f0e645e))
* **frontend:** reload subscription videos when a check ends ([938af02](https://github.com/ZXY101/yt-dlp-z/commit/938af026fc3e420caef1a48a63e3d392b461903b))
* **frontend:** show folder suggestions in a themed list under the field ([b7a31c5](https://github.com/ZXY101/yt-dlp-z/commit/b7a31c5400ffd59796377990bf73789735ae69e9))
* **frontend:** show the pointer cursor on buttons and checkbox labels ([14be42c](https://github.com/ZXY101/yt-dlp-z/commit/14be42c1b9d1c890e444b82e83a9e1cea6acc808))
* **frontend:** use dark native controls in dark mode ([3f23b5e](https://github.com/ZXY101/yt-dlp-z/commit/3f23b5e544d0e938982afbd19c5fa96d702b5280))
* stop stale job updates from overwriting newer job state ([c19d045](https://github.com/ZXY101/yt-dlp-z/commit/c19d045431e1b17befc698b68f8ac1dedcdbd7d7))
* watch channels through the videos tab when the RSS feed fails ([4e08096](https://github.com/ZXY101/yt-dlp-z/commit/4e08096e5a484a0344a9d171ab5b9b630d0b95ac))


### Performance Improvements

* **backend:** try a fast YouTube player first in the link check ([cf54bef](https://github.com/ZXY101/yt-dlp-z/commit/cf54befaed79043c59aa19858ae9c26b6e3086f3))
* **frontend:** check a pasted link without waiting ([21c0b32](https://github.com/ZXY101/yt-dlp-z/commit/21c0b321e68aa559d9ade76dadeb2dee03104ae5))
