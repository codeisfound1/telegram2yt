#!/usr/bin/env python3
“””
telegram-yt-shorts — Build and upload YouTube Shorts from Telegram images.
Entry point / CLI.
“””

import argparse
import logging
import os
import sys

from src.config import Config
from src.telegram_fetcher import TelegramFetcher
from src.video_builder import VideoBuilder
from src.youtube_uploader import YouTubeUploader

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s [%(levelname)s] %(name)s — %(message)s”,
handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(“main”)

def parse_args() -> argparse.Namespace:
p = argparse.ArgumentParser(
description=“Fetch Telegram image → build YouTube Short → upload.”
)

```
# --- Telegram ---
p.add_argument("--tg-token", default=os.getenv("TG_BOT_TOKEN"), help="Telegram Bot token")
p.add_argument(
    "--tg-channels",
    default=os.getenv("TG_CHANNEL_IDS", ""),
    help="Comma-separated channel usernames or IDs (e.g. @mychannel,-1001234567890)",
)
p.add_argument(
    "--tg-strategy",
    choices=["latest", "random"],
    default=os.getenv("TG_STRATEGY", "latest"),
    help="Which message to pick from each channel",
)
p.add_argument(
    "--tg-caption-source",
    choices=["caption", "text"],
    default=os.getenv("TG_CAPTION_SOURCE", "caption"),
    help="Use photo caption or message text as subtitle",
)

# --- Video ---
p.add_argument("--duration", type=float, default=float(os.getenv("VIDEO_DURATION", "30")),
               help="Target video duration in seconds (≤60)")
p.add_argument("--fps", type=int, default=int(os.getenv("VIDEO_FPS", "30")),
               help="Frames per second (24–30)")
p.add_argument("--font-path", default=os.getenv("FONT_PATH"), help="Path to custom .ttf font")

# --- Music ---
p.add_argument(
    "--music-url",
    default=os.getenv(
        "MUSIC_URL",
        "https://archive.org/download/piano_improvisation_study/piano_improvisation_study.mp3",
    ),
    help="URL to royalty-free audio (MP3). Leave empty to use bundled silence.",
)
p.add_argument("--music-volume-db", type=float, default=float(os.getenv("MUSIC_DB", "-12")),
               help="Target music dB level (default -12)")

# --- YouTube ---
p.add_argument("--yt-secrets", default=os.getenv("YT_CLIENT_SECRETS", "client_secrets.json"),
               help="Path to Google OAuth client_secrets.json")
p.add_argument("--yt-token", default=os.getenv("YT_TOKEN_FILE", "yt_token.json"),
               help="Path to cached OAuth token file")
p.add_argument(
    "--title",
    default=os.getenv("YT_TITLE_TEMPLATE", "✨ {channel} | {date}"),
    help="Video title template. Supports {channel}, {date}, {caption_preview}",
)
p.add_argument("--description", default=os.getenv("YT_DESCRIPTION", ""),
               help="Video description")
p.add_argument(
    "--tags",
    default=os.getenv("YT_TAGS", "Shorts,YouTube Shorts,viral"),
    help="Comma-separated tags",
)
p.add_argument(
    "--privacy",
    choices=["public", "unlisted", "private"],
    default=os.getenv("YT_PRIVACY", "public"),
    help="YouTube privacy status",
)
p.add_argument(
    "--category-id",
    default=os.getenv("YT_CATEGORY_ID", "22"),
    help="YouTube category ID (22 = People & Blogs)",
)

# --- Output ---
p.add_argument("--output", default=os.getenv("OUTPUT_FILE", "output_short.mp4"),
               help="Local output MP4 path")
p.add_argument("--no-upload", action="store_true", help="Build video but skip YouTube upload")
p.add_argument("--debug", action="store_true", help="Enable DEBUG logging")

return p.parse_args()
```

def main() -> None:
args = parse_args()

```
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

cfg = Config.from_args(args)
cfg.validate()

log.info("=== Step 1 — Fetch from Telegram ===")
fetcher = TelegramFetcher(cfg)
post = fetcher.fetch()
if not post:
    log.error("No suitable image post found. Aborting.")
    sys.exit(1)
log.info("Fetched post from channel '%s': %s", post.channel, post.caption[:80] if post.caption else "(no caption)")

log.info("=== Step 2 — Build Short ===")
builder = VideoBuilder(cfg)
output_path = builder.build(post, args.output)
log.info("Video written to: %s", output_path)

if args.no_upload:
    log.info("--no-upload set. Done.")
    return

log.info("=== Step 3 — Upload to YouTube ===")
uploader = YouTubeUploader(cfg)
video_id = uploader.upload(output_path, post)
log.info("Uploaded! https://www.youtube.com/shorts/%s", video_id)
```

if **name** == “**main**”:
main()
