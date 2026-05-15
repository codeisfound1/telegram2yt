“”“Build a 9:16 YouTube Short from a Telegram post image + caption.”””

from **future** import annotations

import logging
import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import Config
from .telegram_fetcher import TelegramPost

log = logging.getLogger(**name**)

# Attempt lazy moviepy import (heavy)

try:
from moviepy.editor import (
AudioFileClip,
ColorClip,
CompositeVideoClip,
ImageClip,
concatenate_videoclips,
)
from moviepy.audio.fx.all import audio_normalize, volumex
MOVIEPY_OK = True
except Exception as _e:
log.warning(“moviepy not available: %s”, _e)
MOVIEPY_OK = False

# Royalty-free music — Internet Archive / Public Domain

DEFAULT_MUSIC_URL = (
“https://archive.org/download/piano_improvisation_study/piano_improvisation_study.mp3”
)

# License: Public Domain / Creative Commons Zero — https://archive.org/details/piano_improvisation_study

MUSIC_CACHE = Path(“assets/bg_music.mp3”)
MUSIC_LICENSE_NOTE = (
“Background music source: https://archive.org/details/piano_improvisation_study\n”
“License: Public Domain / CC0\n”
)

CAPTION_WORDS_PER_LINE = 7
CAPTION_LINE_DURATION = 2.5   # seconds each line is displayed
CAPTION_FADE_DURATION = 0.4   # fade-in duration per line
FONT_SIZE_BASE = 64
CAPTION_PADDING = 24
CAPTION_BG_ALPHA = 160          # 0–255

class VideoBuilder:
def **init**(self, cfg: Config):
self.cfg = cfg
self.w = cfg.width
self.h = cfg.height

```
# ------------------------------------------------------------------
# Public
# ------------------------------------------------------------------

def build(self, post: TelegramPost, output_path: str) -> str:
    if not MOVIEPY_OK:
        raise RuntimeError(
            "moviepy is not installed. Run: pip install moviepy"
        )

    log.info("Building %dx%d Short, %.1fs @ %dfps", self.w, self.h, self.cfg.duration, self.cfg.fps)

    # 1. Prepare background image clip
    bg_clip = self._make_background_clip(post.image_path)

    # 2. Prepare caption overlay clips
    caption_clips = self._make_caption_clips(post.caption, self.cfg.duration)

    # 3. Composite
    all_clips = [bg_clip] + caption_clips
    video = CompositeVideoClip(all_clips, size=(self.w, self.h))
    video = video.set_duration(self.cfg.duration)

    # 4. Audio — background music
    audio = self._prepare_audio(self.cfg.duration)
    if audio:
        video = video.set_audio(audio)

    # 5. Render
    log.info("Rendering MP4 → %s …", output_path)
    video.write_videofile(
        output_path,
        fps=self.cfg.fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="tmp_audio.m4a",
        remove_temp=True,
        preset="medium",
        ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p"],
        verbose=False,
        logger=None,
    )
    log.info("Render complete.")
    return output_path

# ------------------------------------------------------------------
# Background image
# ------------------------------------------------------------------

def _make_background_clip(self, image_path: Path) -> "ImageClip":
    log.debug("Preparing background from %s", image_path)
    img = Image.open(image_path).convert("RGB")
    img = self._fit_cover(img, self.w, self.h)
    # Subtle darkening vignette for caption readability
    img = self._apply_vignette(img)
    arr = np.array(img)
    clip = ImageClip(arr).set_duration(self.cfg.duration)
    return clip

def _fit_cover(self, img: Image.Image, w: int, h: int) -> Image.Image:
    """Scale + center-crop to exactly w×h (cover behaviour)."""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(math.ceil(iw * scale)), int(math.ceil(ih * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))

def _apply_vignette(self, img: Image.Image) -> Image.Image:
    """Radial dark vignette to ease caption contrast."""
    arr = np.array(img, dtype=np.float32)
    x = np.linspace(-1, 1, self.w)
    y = np.linspace(-1, 1, self.h)
    xv, yv = np.meshgrid(x, y)
    mask = 1.0 - np.clip(xv**2 + yv**2, 0, 1) * 0.55
    mask = mask[:, :, np.newaxis]
    arr = np.clip(arr * mask, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

# ------------------------------------------------------------------
# Caption clips
# ------------------------------------------------------------------

def _make_caption_clips(self, caption: str, total_duration: float) -> List["ImageClip"]:
    if not caption or not caption.strip():
        log.debug("No caption text — skipping subtitle overlay")
        return []

    lines = self._wrap_text(caption.strip(), CAPTION_WORDS_PER_LINE)
    log.debug("Caption split into %d lines", len(lines))

    font = self._load_font()
    clips = []
    t_start = 1.0  # start 1 s in

    for i, line in enumerate(lines):
        if t_start >= total_duration - 0.5:
            break
        line_dur = min(CAPTION_LINE_DURATION, total_duration - t_start - 0.2)
        img_arr = self._render_caption_frame(line, font)
        clip = (
            ImageClip(img_arr)
            .set_start(t_start)
            .set_duration(line_dur)
            .crossfadein(CAPTION_FADE_DURATION)
            .set_position(("center", int(self.h * 0.72)))
        )
        clips.append(clip)
        t_start += line_dur + 0.15

    return clips

def _render_caption_frame(self, text: str, font: ImageFont.FreeTypeFont) -> np.ndarray:
    """Render one caption line: semi-transparent pill background + white text."""
    # Measure text on a dummy image
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad_x = CAPTION_PADDING * 2
    pad_y = CAPTION_PADDING
    frame_w = min(tw + pad_x * 2, self.w - 40)
    frame_h = th + pad_y * 2

    # Background pill
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = frame_h // 2
    draw.rounded_rectangle(
        [0, 0, frame_w - 1, frame_h - 1],
        radius=radius,
        fill=(0, 0, 0, CAPTION_BG_ALPHA),
    )

    # Text centered
    tx = (frame_w - tw) // 2
    ty = (frame_h - th) // 2
    # Drop shadow
    draw.text((tx + 2, ty + 2), text, font=font, fill=(0, 0, 0, 180))
    # Main text
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))

    return np.array(img)

def _wrap_text(self, text: str, words_per_line: int) -> List[str]:
    words = text.split()
    lines = []
    for i in range(0, len(words), words_per_line):
        lines.append(" ".join(words[i : i + words_per_line]))
    return lines

def _load_font(self) -> ImageFont.FreeTypeFont:
    size = FONT_SIZE_BASE
    if self.cfg.font_path and Path(self.cfg.font_path).exists():
        log.debug("Loading custom font: %s", self.cfg.font_path)
        return ImageFont.truetype(self.cfg.font_path, size)
    # Try common system fonts
    for candidate in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        if Path(candidate).exists():
            log.debug("Using system font: %s", candidate)
            return ImageFont.truetype(candidate, size)
    log.warning("No TTF font found — falling back to PIL default (low quality)")
    return ImageFont.load_default()

# ------------------------------------------------------------------
# Audio
# ------------------------------------------------------------------

def _prepare_audio(self, duration: float) -> Optional["AudioFileClip"]:
    music_path = self._get_music_file()
    if not music_path:
        log.warning("No music available — video will be silent")
        return None

    try:
        clip = AudioFileClip(str(music_path))
        # Loop if shorter than needed
        if clip.duration < duration:
            loops = math.ceil(duration / clip.duration)
            from moviepy.audio.AudioClip import concatenate_audioclips
            clip = concatenate_audioclips([clip] * loops)
        clip = clip.subclip(0, duration)
        # Apply volume adjustment from dB
        linear_vol = 10 ** (self.cfg.music_volume_db / 20.0)
        clip = clip.fx(volumex, linear_vol)
        return clip
    except Exception as exc:
        log.error("Audio preparation failed: %s", exc)
        return None

def _get_music_file(self) -> Optional[Path]:
    if MUSIC_CACHE.exists():
        log.debug("Using cached music: %s", MUSIC_CACHE)
        return MUSIC_CACHE

    url = self.cfg.music_url or DEFAULT_MUSIC_URL
    if not url:
        return None

    log.info("Downloading background music from %s …", url)
    MUSIC_CACHE.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, MUSIC_CACHE)
        # Write license note
        license_file = MUSIC_CACHE.parent / "MUSIC_LICENSE.txt"
        license_file.write_text(MUSIC_LICENSE_NOTE)
        log.info("Music downloaded → %s", MUSIC_CACHE)
        return MUSIC_CACHE
    except Exception as exc:
        log.error("Could not download music: %s", exc)
        return None
```
