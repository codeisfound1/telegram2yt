# GitHub Issue / Copilot Workspace Prompt

## Title

`feat: Telegram → YouTube Shorts pipeline`

## Body

### Summary

Build and upload a YouTube Short automatically from images and captions sourced from Telegram channels using GitHub Actions CI.

### Acceptance Criteria

- [ ] `main.py` CLI works end-to-end: Telegram fetch → video build → YouTube upload.
- [ ] Video is 1080×1920 (9:16), H.264 + AAC, ≤ 60 s, 24–30 fps.
- [ ] Animated line-by-line captions with semi-transparent background rendered via Pillow.
- [ ] Background music mixed at –12 dB; source is CC0 / Public Domain; license note included.
- [ ] YouTube upload is resumable with chunked progress logging and exponential-backoff retries.
- [ ] All credentials (Telegram token, channel IDs, Google OAuth) supplied via ENV / GitHub Secrets.
- [ ] `yt_token.json` can be stored as base64 GitHub Secret for headless CI token refresh.
- [ ] `.github/workflows/build_and_upload.yml` runs on schedule and `workflow_dispatch`.
- [ ] `requirements.txt` lists all dependencies; `README.md` has Quick Start and Secrets setup guide.
- [ ] Optional `FONT_PATH` / `--font-path` for custom TTF.
- [ ] `--no-upload` flag for local testing without uploading.

### Out of Scope

- Telegram user-account (MTProto) access.
- Multiple simultaneous channel uploads in one run.
- Advanced video effects beyond vignette + caption overlay.

### References

- [YouTube Data API v3 — Videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
- [Telegram Bot API — getUpdates](https://core.telegram.org/bots/api#getupdates)
- [MoviePy docs](https://zulko.github.io/moviepy/)
- Background music CC0 source: https://archive.org/details/piano_improvisation_study

-----

### Copilot Workspace Instructions

```
Given the repository structure in this issue, implement:

1. src/telegram_fetcher.py — TelegramFetcher class
   - Uses requests to call Telegram Bot API (no SDK required)
   - Supports getUpdates to read channel_post updates
   - Retries on 429 with Retry-After header
   - Downloads and caches the largest photo size

2. src/video_builder.py — VideoBuilder class
   - Uses moviepy.editor.ImageClip for background
   - Fits image to 1080×1920 with cover crop + vignette
   - Wraps caption into N-word lines; renders each as a Pillow RGBA frame
   - Applies fade-in crossfade per caption line using .crossfadein()
   - Downloads CC0 MP3, loops if short, sets volume to target dB
   - Writes H.264 + AAC MP4 via write_videofile()

3. src/youtube_uploader.py — YouTubeUploader class
   - Loads/refreshes OAuth2 token from yt_token.json
   - Builds video metadata with title template substitution
   - Uses MediaFileUpload(resumable=True) with 5 MB chunks
   - Retries on HTTP 5xx with exponential backoff

4. main.py — argparse CLI wiring Config → Fetcher → Builder → Uploader

5. .github/workflows/build_and_upload.yml
   - Restores client_secrets.json and yt_token.json from base64 Secrets
   - Runs pipeline with ENV vars from Secrets
   - Uploads output_short.mp4 as workflow artifact
```
