“”“Upload a video to YouTube Shorts using Data API v3 with resumable upload.”””

from **future** import annotations

import datetime
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from .config import Config
from .telegram_fetcher import TelegramPost

log = logging.getLogger(**name**)

SCOPES = [“https://www.googleapis.com/auth/youtube.upload”]
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB chunks
MAX_RETRIES = 5
RETRIABLE_STATUS_CODES = {500, 502, 503, 504}

class YouTubeUploader:
def **init**(self, cfg: Config):
self.cfg = cfg

```
# ------------------------------------------------------------------
# Public
# ------------------------------------------------------------------

def upload(self, video_path: str, post: TelegramPost) -> str:
    """Upload video; return YouTube video ID."""
    service = self._build_service()
    title = self._render_title(post)
    body = {
        "snippet": {
            "title": title[:100],          # YouTube max
            "description": self._build_description(post),
            "tags": self.cfg.tags[:500],    # API limit: 500 tags, each ≤500 chars
            "categoryId": self.cfg.category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": self.cfg.privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    log.info("Uploading '%s' (%s) …", title, self.cfg.privacy)

    media = MediaFileUpload(
        video_path,
        chunksize=CHUNK_SIZE,
        resumable=True,
        mimetype="video/mp4",
    )
    request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    video_id = self._resumable_upload(request, Path(video_path).stat().st_size)
    return video_id

# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------

def _build_service(self):
    creds = self._load_credentials()
    return build("youtube", "v3", credentials=creds, cache_discovery=False)

def _load_credentials(self) -> Credentials:
    token_path = Path(self.cfg.yt_token)
    creds: Optional[Credentials] = None

    # 1. Try loading existing token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            log.debug("Loaded existing OAuth token from %s", token_path)
        except Exception as exc:
            log.warning("Could not load token file: %s", exc)

    # 2. Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        log.info("Refreshing OAuth token…")
        try:
            creds.refresh(Request())
            self._save_token(creds, token_path)
            return creds
        except Exception as exc:
            log.warning("Token refresh failed: %s — will re-authenticate", exc)
            creds = None

    if creds and creds.valid:
        return creds

    # 3. Interactive OAuth (needed for first run; incompatible with headless CI)
    secrets = Path(self.cfg.yt_secrets)
    if not secrets.exists():
        raise FileNotFoundError(
            f"client_secrets.json not found at '{secrets}'. "
            "Download it from Google Cloud Console → APIs & Services → Credentials."
        )

    log.info(
        "Starting OAuth flow. In CI, run locally first to generate '%s', "
        "then store it as a GitHub Secret (base64-encoded).",
        token_path,
    )
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    # In CI: set OAUTH_REDIRECT_PORT or use --no-browser
    port = int(os.getenv("OAUTH_PORT", "0"))
    creds = flow.run_local_server(port=port, open_browser=True)
    self._save_token(creds, token_path)
    return creds

def _save_token(self, creds: Credentials, path: Path) -> None:
    path.write_text(creds.to_json())
    log.debug("Token saved → %s", path)

# ------------------------------------------------------------------
# Resumable upload with exponential backoff
# ------------------------------------------------------------------

def _resumable_upload(self, request, file_size: int) -> str:
    response = None
    error = None
    retry = 0
    bytes_uploaded = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                bytes_uploaded = status.resumable_progress
                pct = bytes_uploaded / file_size * 100
                log.info("Upload progress: %.1f%% (%s / %s)", pct,
                         _fmt_bytes(bytes_uploaded), _fmt_bytes(file_size))
        except HttpError as exc:
            if exc.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {exc.resp.status}: {exc}"
            else:
                raise
        except Exception as exc:
            error = str(exc)

        if error:
            retry += 1
            if retry > MAX_RETRIES:
                raise RuntimeError(f"Upload failed after {MAX_RETRIES} retries: {error}")
            wait = 2 ** retry
            log.warning("Upload error (attempt %d/%d): %s — retrying in %ds", retry, MAX_RETRIES, error, wait)
            time.sleep(wait)
            error = None

    video_id = response.get("id", "")
    log.info("Upload complete! Video ID: %s", video_id)
    return video_id

# ------------------------------------------------------------------
# Metadata helpers
# ------------------------------------------------------------------

def _render_title(self, post: TelegramPost) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")
    caption_preview = (post.caption[:40] + "…") if len(post.caption) > 40 else post.caption
    channel_clean = post.channel.strip("@")
    return (
        self.cfg.title_template
        .replace("{channel}", channel_clean)
        .replace("{date}", today)
        .replace("{caption_preview}", caption_preview)
    )

def _build_description(self, post: TelegramPost) -> str:
    parts = []
    if self.cfg.description:
        parts.append(self.cfg.description)
    if post.caption:
        parts.append(post.caption)
    parts.append("\n\n#Shorts #YouTubeShorts")
    return "\n\n".join(parts)
```

def _fmt_bytes(n: int) -> str:
for unit in (“B”, “KB”, “MB”, “GB”):
if n < 1024:
return f”{n:.1f} {unit}”
n /= 1024
return f”{n:.1f} TB”
