“”“Configuration dataclass assembled from CLI args + ENV.”””

from **future** import annotations

import argparse
import sys
import logging
from dataclasses import dataclass, field
from typing import List, Optional

log = logging.getLogger(**name**)

MAX_DURATION = 60.0  # YouTube Shorts hard limit
MIN_FPS, MAX_FPS = 24, 30
WIDTH, HEIGHT = 1080, 1920  # 9:16

@dataclass
class Config:
# Telegram
tg_token: str
tg_channels: List[str]
tg_strategy: str = “latest”
tg_caption_source: str = “caption”

```
# Video
duration: float = 30.0
fps: int = 30
font_path: Optional[str] = None
width: int = WIDTH
height: int = HEIGHT

# Music
music_url: str = ""
music_volume_db: float = -12.0

# YouTube
yt_secrets: str = "client_secrets.json"
yt_token: str = "yt_token.json"
title_template: str = "✨ {channel} | {date}"
description: str = ""
tags: List[str] = field(default_factory=list)
privacy: str = "public"
category_id: str = "22"

@classmethod
def from_args(cls, args: argparse.Namespace) -> "Config":
    channels = [c.strip() for c in (args.tg_channels or "").split(",") if c.strip()]
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    return cls(
        tg_token=args.tg_token or "",
        tg_channels=channels,
        tg_strategy=args.tg_strategy,
        tg_caption_source=args.tg_caption_source,
        duration=min(args.duration, MAX_DURATION),
        fps=max(MIN_FPS, min(args.fps, MAX_FPS)),
        font_path=args.font_path,
        music_url=args.music_url,
        music_volume_db=args.music_volume_db,
        yt_secrets=args.yt_secrets,
        yt_token=args.yt_token,
        title_template=args.title,
        description=args.description,
        tags=tags,
        privacy=args.privacy,
        category_id=args.category_id,
    )

def validate(self) -> None:
    errors = []
    if not self.tg_token:
        errors.append("TG_BOT_TOKEN / --tg-token is required")
    if not self.tg_channels:
        errors.append("TG_CHANNEL_IDS / --tg-channels is required")
    if self.duration <= 0 or self.duration > MAX_DURATION:
        errors.append(f"--duration must be 1–{MAX_DURATION}")
    if errors:
        for e in errors:
            log.error("Config error: %s", e)
        sys.exit(1)
    log.debug("Config validated: channels=%s duration=%.1fs fps=%d", self.tg_channels, self.duration, self.fps)
```
