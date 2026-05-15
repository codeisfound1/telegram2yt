“”“Fetch the latest image post from Telegram channels via Bot API (HTTPS only).”””

from **future** import annotations

import io
import logging
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import requests

from .config import Config

log = logging.getLogger(**name**)

TG_API = “https://api.telegram.org/bot{token}/{method}”
TG_FILE = “https://api.telegram.org/file/bot{token}/{file_path}”
DOWNLOAD_DIR = Path(“downloads”)
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds

@dataclass
class TelegramPost:
channel: str
caption: str
image_path: Path
message_id: int

class TelegramFetcher:
def **init**(self, cfg: Config):
self.cfg = cfg
DOWNLOAD_DIR.mkdir(exist_ok=True)

```
# ------------------------------------------------------------------
# Public
# ------------------------------------------------------------------

def fetch(self) -> Optional[TelegramPost]:
    """Try each channel in order; return the first successful post."""
    for channel in self.cfg.tg_channels:
        log.info("Fetching from channel: %s", channel)
        try:
            post = self._fetch_channel(channel)
            if post:
                return post
        except Exception as exc:
            log.warning("Failed to fetch from %s: %s", channel, exc)
    return None

# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _fetch_channel(self, channel: str) -> Optional[TelegramPost]:
    messages = self._get_messages(channel)
    photo_messages = [m for m in messages if m.get("photo")]

    if not photo_messages:
        log.warning("No photo messages found in %s", channel)
        return None

    if self.cfg.tg_strategy == "random":
        msg = random.choice(photo_messages)
    else:  # latest
        msg = photo_messages[-1]

    caption = self._extract_caption(msg)
    image_path = self._download_photo(msg, channel)
    if not image_path:
        return None

    return TelegramPost(
        channel=channel,
        caption=caption,
        image_path=image_path,
        message_id=msg["message_id"],
    )

def _get_messages(self, channel: str) -> List[dict]:
    """getUpdates is only for bots receiving messages. For public channels
    we use getChat + getChatHistory via forwardFrom workaround.
    We use getUpdates (bot must be a member/admin of the channel)."""
    # Try channel export first (works if bot is channel admin)
    data = self._api_call("getUpdates", params={"limit": 100, "allowed_updates": '["channel_post"]'})
    if data and data.get("result"):
        channel_posts = []
        for update in data["result"]:
            post = update.get("channel_post", {})
            chat = post.get("chat", {})
            chat_id = str(chat.get("id", ""))
            username = chat.get("username", "")
            # Match by @username or numeric ID
            if username and (f"@{username}" == channel or username == channel.lstrip("@")):
                channel_posts.append(post)
            elif chat_id == str(channel):
                channel_posts.append(post)
        if channel_posts:
            log.debug("Found %d posts via getUpdates for %s", len(channel_posts), channel)
            return channel_posts

    # Fallback: use forwardMessages approach or getChatHistory (bot must be admin)
    log.debug("getUpdates returned no posts for %s; trying getChatAdministrators probe", channel)
    # Resolve channel to ID
    chat_info = self._api_call("getChat", params={"chat_id": channel})
    if not chat_info or not chat_info.get("result"):
        raise RuntimeError(f"Cannot resolve channel {channel}")

    chat_id = chat_info["result"]["id"]
    # Fetch recent messages by calling copyMessage trick: not available without message IDs.
    # Best approach with Bot API: bot must be subscribed to channel_post updates.
    # We return empty and let the caller handle it.
    log.warning(
        "Bot may not be receiving channel_post updates from %s. "
        "Ensure the bot is an admin of the channel.", channel
    )
    return []

def _extract_caption(self, msg: dict) -> str:
    if self.cfg.tg_caption_source == "text":
        return msg.get("text", "") or msg.get("caption", "")
    return msg.get("caption", "") or msg.get("text", "")

def _download_photo(self, msg: dict, channel: str) -> Optional[Path]:
    """Download the largest photo size from a message."""
    photos = msg.get("photo", [])
    if not photos:
        return None
    # Largest size is the last element
    file_id = photos[-1]["file_id"]

    file_info = self._api_call("getFile", params={"file_id": file_id})
    if not file_info or not file_info.get("result"):
        log.error("Could not get file info for file_id=%s", file_id)
        return None

    file_path = file_info["result"]["file_path"]
    url = TG_FILE.format(token=self.cfg.tg_token, file_path=file_path)

    dest = DOWNLOAD_DIR / f"{channel.strip('@')}_{msg['message_id']}.jpg"
    if dest.exists():
        log.debug("Using cached photo: %s", dest)
        return dest

    log.info("Downloading photo from Telegram…")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=30, stream=True)
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=65536):
                    fh.write(chunk)
            log.info("Saved photo → %s (%.1f KB)", dest, dest.stat().st_size / 1024)
            return dest
        except requests.RequestException as exc:
            log.warning("Download attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
    return None

def _api_call(self, method: str, params: Optional[dict] = None, attempt: int = 1) -> Optional[dict]:
    url = TG_API.format(token=self.cfg.tg_token, method=method)
    try:
        resp = requests.get(url, params=params or {}, timeout=20)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            log.warning("Rate limited by Telegram. Waiting %ds…", retry_after)
            time.sleep(retry_after)
            if attempt <= MAX_RETRIES:
                return self._api_call(method, params, attempt + 1)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        log.error("Telegram API call failed [%s]: %s", method, exc)
        return None
```
