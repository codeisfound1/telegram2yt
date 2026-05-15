# telegram-yt-shorts

**Fetch an image from Telegram → build a 9:16 YouTube Short → upload automatically.**

```
Telegram Channel  ──►  Python pipeline  ──►  YouTube Shorts
(image + caption)       (MoviePy + Pillow)     (Data API v3)
```

-----

## Features

|Feature         |Detail                                                           |
|----------------|-----------------------------------------------------------------|
|Telegram source |Bot API — latest, random, or oldest unread image                 |
|Video format    |1080 × 1920 (9:16), H.264 + AAC, 24–30 fps, ≤ 60 s               |
|Caption overlay |Line-by-line fade-in, semi-transparent pill background           |
|Background music|CC0 track auto-downloaded; mixed to configurable dB              |
|YouTube upload  |Resumable chunked upload, progress logging, retry logic          |
|CI-ready        |GitHub Actions workflow included; no interactive auth at run-time|

-----

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/your-org/telegram-yt-shorts.git
cd telegram-yt-shorts

# System dependency (macOS / Ubuntu)
brew install ffmpeg          # macOS
sudo apt-get install ffmpeg  # Ubuntu/Debian

pip install -r requirements.txt
```

### 2. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) → `/newbot`.
1. Copy the **bot token**.
1. Add the bot as an **admin** of your channel(s) so it receives `channel_post` updates.
1. Note the channel username(s), e.g. `@mychannel`.

### 3. Create Google OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
1. Create a project → **APIs & Services → Library** → enable **YouTube Data API v3**.
1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
- Application type: **Desktop app**.
1. Download the JSON → save as **`client_secrets.json`** in the repo root.

### 4. First-time OAuth (local, one-time)

```bash
# This opens a browser to authorise your YouTube account.
# It saves yt_token.json — keep this file secret.
python main.py \
  --tg-token "YOUR_BOT_TOKEN" \
  --tg-channels "@mychannel" \
  --no-upload   # optional: build video only on first test
```

After the browser flow completes, `yt_token.json` is created.

### 5. Run the full pipeline

```bash
python main.py \
  --tg-token  "YOUR_BOT_TOKEN" \
  --tg-channels "@mychannel" \
  --duration  30 \
  --title     "✨ {channel} | {date}" \
  --privacy   public
```

-----

## CLI Reference

|Flag / ENV                                 |Default                      |Description                                        |
|-------------------------------------------|-----------------------------|---------------------------------------------------|
|`--tg-token` / `TG_BOT_TOKEN`              |*(required)*                 |Telegram Bot token                                 |
|`--tg-channels` / `TG_CHANNEL_IDS`         |*(required)*                 |Comma-separated `@channel` or numeric IDs          |
|`--tg-strategy` / `TG_STRATEGY`            |`latest`                     |`latest` or `random`                               |
|`--tg-caption-source` / `TG_CAPTION_SOURCE`|`caption`                    |`caption` or `text`                                |
|`--duration` / `VIDEO_DURATION`            |`30`                         |Seconds (1–60)                                     |
|`--fps` / `VIDEO_FPS`                      |`30`                         |24–30                                              |
|`--font-path` / `FONT_PATH`                |*(system font)*              |Path to custom `.ttf`                              |
|`--music-url` / `MUSIC_URL`                |CC0 Internet Archive track   |URL to MP3                                         |
|`--music-volume-db` / `MUSIC_DB`           |`-12`                        |dB level for music                                 |
|`--yt-secrets` / `YT_CLIENT_SECRETS`       |`client_secrets.json`        |OAuth secrets file                                 |
|`--yt-token` / `YT_TOKEN_FILE`             |`yt_token.json`              |Cached token file                                  |
|`--title` / `YT_TITLE_TEMPLATE`            |`✨ {channel} | {date}`       |Supports `{channel}`, `{date}`, `{caption_preview}`|
|`--description` / `YT_DESCRIPTION`         |*(empty)*                    |Video description                                  |
|`--tags` / `YT_TAGS`                       |`Shorts,YouTube Shorts,viral`|Comma-separated                                    |
|`--privacy` / `YT_PRIVACY`                 |`public`                     |`public`, `unlisted`, `private`                    |
|`--category-id` / `YT_CATEGORY_ID`         |`22`                         |YouTube category (22 = People & Blogs)             |
|`--output` / `OUTPUT_FILE`                 |`output_short.mp4`           |Local output path                                  |
|`--no-upload`                              |off                          |Build video, skip upload                           |
|`--debug`                                  |off                          |Verbose logging                                    |

-----

## GitHub Secrets Setup

Go to **Settings → Secrets and variables → Actions → New repository secret**:

|Secret name            |Value                                                |
|-----------------------|-----------------------------------------------------|
|`TG_BOT_TOKEN`         |Your Telegram bot token                              |
|`TG_CHANNEL_IDS`       |e.g. `@mychannel` or `-1001234567890`                |
|`YT_CLIENT_SECRETS_B64`|`base64 -w 0 client_secrets.json`                    |
|`YT_TOKEN_B64`         |`base64 -w 0 yt_token.json` *(after first local run)*|

### Encode secrets on Linux / macOS

```bash
base64 -w 0 client_secrets.json   # → paste as YT_CLIENT_SECRETS_B64
base64 -w 0 yt_token.json         # → paste as YT_TOKEN_B64
```

On macOS use `base64 -i client_secrets.json` (no `-w 0` needed).

> **Important:** The OAuth token contains a `refresh_token`. As long as you keep the Google Cloud
> project active and the token is refreshed at least once every 6 months, you don’t need to
> re-authorise. The workflow prints the updated base64 token in the Actions log; update the secret
> if it changes.

-----

## GitHub Actions

The included workflow (`.github/workflows/build_and_upload.yml`) runs:

- **Daily at 10:00 UTC** (cron).
- **On-demand** via `workflow_dispatch` with `privacy` and `tg_strategy` inputs.

### Manual trigger

```
Actions → "Telegram → YouTube Short" → Run workflow → choose inputs
```

-----

## Background Music

The pipeline downloads a **CC0 / Public Domain** piano track from the Internet Archive on first run
and caches it to `assets/bg_music.mp3`.

**Source:** https://archive.org/details/piano_improvisation_study  
**License:** Public Domain / Creative Commons Zero (CC0)

To use a different track, set `--music-url` or `MUSIC_URL` to any direct MP3 URL.  
A license note is written to `assets/MUSIC_LICENSE.txt`.

-----

## Custom Font

Place a `.ttf` file in the repo and set:

```bash
export FONT_PATH=fonts/MyFont-Bold.ttf
```

or pass `--font-path fonts/MyFont-Bold.ttf`.

-----

## Project Structure

```
telegram-yt-shorts/
├── main.py                        # CLI entry point
├── src/
│   ├── config.py                  # Config dataclass
│   ├── telegram_fetcher.py        # Telegram Bot API fetcher
│   ├── video_builder.py           # MoviePy + Pillow video pipeline
│   └── youtube_uploader.py        # YouTube Data API v3 uploader
├── assets/
│   └── bg_music.mp3               # Cached CC0 music (auto-downloaded)
├── downloads/                     # Cached Telegram images
├── .github/workflows/
│   └── build_and_upload.yml       # CI/CD pipeline
├── requirements.txt
└── README.md
```

-----

## Troubleshooting

|Problem                        |Fix                                                                                               |
|-------------------------------|--------------------------------------------------------------------------------------------------|
|`No photo messages found`      |Ensure the bot is a channel **admin** and has received at least one image post since it was added.|
|`client_secrets.json not found`|Download OAuth credentials from Google Cloud Console.                                             |
|`Token expired`                |Re-run locally to refresh, then update `YT_TOKEN_B64` secret.                                     |
|`ffmpeg not found`             |Install with `apt-get install ffmpeg` or `brew install ffmpeg`.                                   |
|Upload quota exceeded          |YouTube Data API v3 default quota is 10 000 units/day. One upload costs ~1 600 units.             |

-----

## License

MIT — see <LICENSE>.  
Background music: Public Domain / CC0 (see `assets/MUSIC_LICENSE.txt`).
