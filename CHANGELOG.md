# Changelog

## [0.1.1](https://github.com/ZXY101/yt-dlp-z/compare/yt-dlp-z-v0.1.0...yt-dlp-z-v0.1.1) (2026-11-03)


### Features

* **backend:** channel picture and banner for media servers ([664c95a](https://github.com/ZXY101/yt-dlp-z/commit/664c95a4bc59a69e7e5f6547e72238024917ca5c))
* delete a download's files, skip videos for good, and show disk usage ([6292433](https://github.com/ZXY101/yt-dlp-z/commit/6292433167bf520628ef8ef0b4161b0b5eb8d3ad))
* **frontend:** expand a subscription to list its downloads and recordings ([bd3388e](https://github.com/ZXY101/yt-dlp-z/commit/bd3388eb8d7d6da244f25c395dd7c06e7543147c))
* **frontend:** new logo, favicon and home-screen icon ([ffc360e](https://github.com/ZXY101/yt-dlp-z/commit/ffc360ec125fc60ef25ebd57b9e3de239759c84a))
* get PO tokens from a bgutil provider ([9414056](https://github.com/ZXY101/yt-dlp-z/commit/941405632684d7f01ebeda2c75b152ea44d31d52))
* optionally delete a subscription's downloads after N days ([233e194](https://github.com/ZXY101/yt-dlp-z/commit/233e1942e0721d5acc2faac4a05c2052da5c55ed))
* optionally download a stream's VOD after recording it ([0ba7207](https://github.com/ZXY101/yt-dlp-z/commit/0ba720770faeb2b508c2a6f4ca04b93c74a41aa3))
* separate sub-folder, file name and media-server file settings ([640dd11](https://github.com/ZXY101/yt-dlp-z/commit/640dd118d8d025c672c09d60a4f3098d59d9c6f0))
* watch playlists as well as channels ([a1f0da4](https://github.com/ZXY101/yt-dlp-z/commit/a1f0da4635450e02d93932053ccd285881a2a4f0))


### Bug Fixes

* **backend:** keep the date out of recording titles ([00a35aa](https://github.com/ZXY101/yt-dlp-z/commit/00a35aaf371c4d53a58c70159b01dc163ce58e8b))
* **backend:** leave recording parts that are already numbered alone ([afb221e](https://github.com/ZXY101/yt-dlp-z/commit/afb221e1ffc789d73c49286432a43b6994c5dc7e))
* **backend:** number recording parts only once a second part starts ([b44f859](https://github.com/ZXY101/yt-dlp-z/commit/b44f859338d19cb9d178f7d3dac6ca5219fca4d4))
* **backend:** stop browsers showing the previous release after an update ([d52628c](https://github.com/ZXY101/yt-dlp-z/commit/d52628c1966b80432b0208a41e7db37801ffd77a))
* continue recordings when YouTube's stream links expire ([3e91816](https://github.com/ZXY101/yt-dlp-z/commit/3e9181673fbf23dc277280890db3fe58940e8516))
* **frontend:** full-screen options dialog with a compact toolbar on phones ([9b08993](https://github.com/ZXY101/yt-dlp-z/commit/9b089934e23b4408bc082566bb55d5cecdc81f2f))
* **frontend:** keep dialog content within the screen on phones ([273ba46](https://github.com/ZXY101/yt-dlp-z/commit/273ba462a60a92440523059ebd76940bd5a97d2f))
* recordings that end or wait, and CI hangs ([b7edc6f](https://github.com/ZXY101/yt-dlp-z/commit/b7edc6f1076b170e8ec3c6eb68bca3c65cd6e589))

## 0.1.0 (2026-10-31)


### ⚠ BREAKING CHANGES

* the server now listens on 9742 by default (YTDLPZ_PORT still overrides it); the Docker image exposes 9742.

### Features

* allow setting the admin password with YTDLPZ_ADMIN_PASSWORD ([53161e5](https://github.com/ZXY101/yt-dlp-z/commit/53161e525c7e5c5de24359c61f6bf87c58f116c8))
* **backend:** add download jobs with live progress and yt-dlp option schema ([96acfac](https://github.com/ZXY101/yt-dlp-z/commit/96acfac51dff3d7c6aaae7725efe9b012b18eb16))
* **backend:** add FastAPI server with first-run setup and login ([987bf1d](https://github.com/ZXY101/yt-dlp-z/commit/987bf1d135738e82a677e88d8a5221aa23f69415))
* **backend:** add openapi command that prints the API schema ([000f4d2](https://github.com/ZXY101/yt-dlp-z/commit/000f4d2031941486460691f75ef98496149d7fb0))
* **backend:** add presets API ([5fc5fb5](https://github.com/ZXY101/yt-dlp-z/commit/5fc5fb5a82274b347561ab97a825112d994c4f51))
* **backend:** change the download folder and download limit at runtime ([10ae432](https://github.com/ZXY101/yt-dlp-z/commit/10ae432875fbaf64ddbfa932080c45f05ba6d944))
* **backend:** check daily for a newer yt-dlp and optionally install it ([5bdf1db](https://github.com/ZXY101/yt-dlp-z/commit/5bdf1db30645cb6bbf738d4f4184906d52d626e0))
* **backend:** check links before downloading and record streams on demand ([febce01](https://github.com/ZXY101/yt-dlp-z/commit/febce016744cb85b3dad068f1986c5a55908c30f))
* **backend:** record live and upcoming streams from subscriptions ([a8cd43e](https://github.com/ZXY101/yt-dlp-z/commit/a8cd43eb2a20f949355312a20bcc08d6e58cefa1))
* **backend:** restart interrupted recordings after a restart ([e933a66](https://github.com/ZXY101/yt-dlp-z/commit/e933a6643e87c63187233c7c59b1b24b6a2df60c))
* **backend:** split, limit and safely stop recordings ([150007d](https://github.com/ZXY101/yt-dlp-z/commit/150007d24dd28ea866a14a33de57cb59809a274d))
* **backend:** sweep the streams tab for streams the feed missed ([877d05a](https://github.com/ZXY101/yt-dlp-z/commit/877d05aca2aaa146850efd8a9fd9a4fbaa8e9579))
* **backend:** update yt-dlp from the app ([e9f0a48](https://github.com/ZXY101/yt-dlp-z/commit/e9f0a480317e2efd625593cde292e8bfdc9c8a48))
* **backend:** upload cookies files and use them for downloads ([693fc78](https://github.com/ZXY101/yt-dlp-z/commit/693fc78d87055db5c56b2adb3b39ddfefd654653))
* **backend:** watch YouTube channels and queue their new uploads ([7fdd628](https://github.com/ZXY101/yt-dlp-z/commit/7fdd628a0ef1c217d928db4d02a166d749d39680))
* change the default port from 8080 to 9742 ([c5feac9](https://github.com/ZXY101/yt-dlp-z/commit/c5feac9c94d9b422a8b66fab2f2db005b632f525))
* **frontend:** add download form, live queue and setup warnings ([2e0cbbb](https://github.com/ZXY101/yt-dlp-z/commit/2e0cbbbd1dc1f8ce8afac03bb334ec8832aab54a))
* **frontend:** add presets, cookies and settings pages and an options editor ([6688ba3](https://github.com/ZXY101/yt-dlp-z/commit/6688ba38099f9864e0f0bdb1034dc0352c6eb22f))
* **frontend:** add React app with first-run setup, login and app shell ([d0ba7d4](https://github.com/ZXY101/yt-dlp-z/commit/d0ba7d41cd436c1d38dcd56cebafa1764a46ed67))
* **frontend:** add the Subscriptions page and the channel limit setting ([994d0d3](https://github.com/ZXY101/yt-dlp-z/commit/994d0d3c0e651025e5ca3788cfc116f9b5061b9c))
* **frontend:** ask before downloading a whole playlist ([9102e71](https://github.com/ZXY101/yt-dlp-z/commit/9102e715f2aa220fbe071f5347c88ca2d9d61219))
* **frontend:** check links before downloading and record streams ([8da4890](https://github.com/ZXY101/yt-dlp-z/commit/8da4890a406903519656b1420a88b3b054ef20be))
* **frontend:** link the app name in the header to the download page ([8669a2b](https://github.com/ZXY101/yt-dlp-z/commit/8669a2b45c55fb881b75253db5cf83584e73991c))
* **frontend:** make Download the home page and drop the dashboard ([6680439](https://github.com/ZXY101/yt-dlp-z/commit/66804391d082583cce0ce365457e83d287b3bc1a))
* **frontend:** make empty states clickable ([0f94af6](https://github.com/ZXY101/yt-dlp-z/commit/0f94af6dfd4088c189a2791147b3d7ca212f172f))
* **frontend:** recording settings and parts in the queue ([ad8e639](https://github.com/ZXY101/yt-dlp-z/commit/ad8e63986bfbcb7826412cfeb2f117cc6ae93d8a))
* **frontend:** show all yt-dlp options in a dialog with group tabs ([f10a7f2](https://github.com/ZXY101/yt-dlp-z/commit/f10a7f2518febe47e56377647ddaf4302bb0e4b9))
* **frontend:** show available yt-dlp updates and an auto-update option ([ec26a05](https://github.com/ZXY101/yt-dlp-z/commit/ec26a052bca71e534fa10320204cb767d2d5c87f))
* **frontend:** show scheduled and running recordings ([c942246](https://github.com/ZXY101/yt-dlp-z/commit/c9422460710db824f9e017dc6f1c627ad25b80cd))
* **frontend:** update yt-dlp from Settings ([9205b0c](https://github.com/ZXY101/yt-dlp-z/commit/9205b0c8c776c055a5bcf91a8c55c06a0a708c32))
* media-server output per preset ([c9d9bb7](https://github.com/ZXY101/yt-dlp-z/commit/c9d9bb7ff5548bb98917cd4ef6e483967a3ab53b))
* ntfy notifications ([2ca8e82](https://github.com/ZXY101/yt-dlp-z/commit/2ca8e8290af84f2d4dc366cb72755b54eb5f68b0))
* presets per kind of link with recording settings ([8bf4f91](https://github.com/ZXY101/yt-dlp-z/commit/8bf4f91b208d47856b43ee323dc4b9d53c867f77))
* proxy pool ([9c50c47](https://github.com/ZXY101/yt-dlp-z/commit/9c50c47407744ce190e28d7beb25e593e8447623))
* record the first hours of streams found after running long ([4ffb372](https://github.com/ZXY101/yt-dlp-z/commit/4ffb372250c865dd15e9a62898d50ebe3ec28285))
* suggest existing folders in the "Save to" field ([bb1c54d](https://github.com/ZXY101/yt-dlp-z/commit/bb1c54d347021ea123a4202fe5d50ee4c4fe38f5))


### Bug Fixes

* **backend:** don't let the link check pass unavailable videos ([081e8f3](https://github.com/ZXY101/yt-dlp-z/commit/081e8f3ab3995a2bdcf652c849b5334ad83edf04))
* **backend:** keep no copy when an update matches the bundled yt-dlp ([aab63ec](https://github.com/ZXY101/yt-dlp-z/commit/aab63eca7397029d16a744f4dac57c552dceebf7))
* **backend:** read upcoming streams instead of failing on them ([343ebe8](https://github.com/ZXY101/yt-dlp-z/commit/343ebe83838b346b4d0b09aaed01a6f27f186389))
* **backend:** show progress of recordings ([3917638](https://github.com/ZXY101/yt-dlp-z/commit/3917638a76f2c6d34f1ff0bdcfe3122d8d7b94db))
* **backend:** show progress of recordings joined mid-stream ([f788a67](https://github.com/ZXY101/yt-dlp-z/commit/f788a6770484dcabf9a6869011b44e46a905fb2a))
* **backend:** start every new job with an empty log ([8d034f2](https://github.com/ZXY101/yt-dlp-z/commit/8d034f201e4af6b67ac6d2a95fa7de50f0bbc25f))
* **backend:** stop the yt-dlp options reader when the app shuts down ([1b5a71e](https://github.com/ZXY101/yt-dlp-z/commit/1b5a71e5872eabc2bae66c2ad4bb2d6705b6de77))
* **frontend:** center checkbox rows that have no description ([bd86327](https://github.com/ZXY101/yt-dlp-z/commit/bd863279267aa61a334252371c3c15d14871b8f4))
* **frontend:** give the queue the same width as other pages ([4760bb5](https://github.com/ZXY101/yt-dlp-z/commit/4760bb5b362f5b777ee334af73616d6f37276dcb))
* **frontend:** line checkbox labels up with the box ([e475181](https://github.com/ZXY101/yt-dlp-z/commit/e475181fff3af61e0ba5df7bf14213fdc2e24b83))
* **frontend:** make dropdown options readable in dark mode ([514941f](https://github.com/ZXY101/yt-dlp-z/commit/514941f60b1ceac35e13370a1bbf901ff457770e))
* **frontend:** reload subscription videos when a check ends ([0028475](https://github.com/ZXY101/yt-dlp-z/commit/0028475e5eab8cebb7cb3e364ec08d4ccc0910ea))
* **frontend:** show folder suggestions in a themed list under the field ([e78474f](https://github.com/ZXY101/yt-dlp-z/commit/e78474f2e3824bae24bdd1786022a3996abaaa87))
* **frontend:** show the pointer cursor on buttons and checkbox labels ([7bcf8fb](https://github.com/ZXY101/yt-dlp-z/commit/7bcf8fb0b5997210238fd9afdfa82c719ac7387b))
* **frontend:** use dark native controls in dark mode ([1fee027](https://github.com/ZXY101/yt-dlp-z/commit/1fee02727e474be14fc4ef1e4d30e5d097d4b0b1))
* stop stale job updates from overwriting newer job state ([4a5ce54](https://github.com/ZXY101/yt-dlp-z/commit/4a5ce5413ede0c6c6c869554cf4dc3e74e0cc4b0))
* watch channels through the videos tab when the RSS feed fails ([593ff45](https://github.com/ZXY101/yt-dlp-z/commit/593ff45d41263618ae4430ce50fda7b1ae440c3f))


### Performance Improvements

* **backend:** try a fast YouTube player first in the link check ([7a4136d](https://github.com/ZXY101/yt-dlp-z/commit/7a4136df02b3101331c5a7d8647bd0fbde0d15bc))
* **frontend:** check a pasted link without waiting ([ff26ee4](https://github.com/ZXY101/yt-dlp-z/commit/ff26ee4e93098d8c86d80193e8e10c1589e335f9))
