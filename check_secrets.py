#!/usr/bin/env python3
"""
check_secrets.py — Diagnose client_secrets.json and print a working auth URL.

Usage:
    python check_secrets.py
    python check_secrets.py --secrets path/to/client_secrets.json
"""

import argparse
import json
import sys
import urllib.parse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets", default="client_secrets.json")
    args = parser.parse_args()

    path = Path(args.secrets)
    if not path.exists():
        print(f"ERROR: {path} not found.")
        sys.exit(1)

    raw = json.loads(path.read_text())
    print("Keys in file:", list(raw.keys()))
    print()

    client_info = raw.get("installed") or raw.get("web")
    if not client_info:
        print("ERROR: neither 'installed' nor 'web' key found.")
        print("Full file contents:")
        print(json.dumps(raw, indent=2))
        sys.exit(1)

    client_id     = client_info.get("client_id", "")
    client_secret = client_info.get("client_secret", "")
    redirect_uris = client_info.get("redirect_uris", [])

    print(f"Type:          {'installed' if 'installed' in raw else 'web'}")
    print(f"client_id:     {client_id[:40]}..." if len(client_id) > 40 else f"client_id:     {client_id!r}")
    print(f"client_secret: {client_secret[:6]}..." if client_secret else "client_secret: (empty!)")
    print(f"redirect_uris: {redirect_uris}")
    print()

    if not client_id:
        print("ERROR: client_id is empty — re-download client_secrets.json from Google Cloud Console.")
        sys.exit(1)

    if not client_secret:
        print("ERROR: client_secret is empty.")
        sys.exit(1)

    SCOPE        = "https://www.googleapis.com/auth/youtube.upload"
    REDIRECT_URI = "http://localhost"

    params = {
        "client_id":     client_id,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPE,
        "access_type":   "offline",
        "prompt":        "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    print("=" * 64)
    print("Auth URL (open this in your browser):")
    print()
    print(auth_url)
    print()
    print("=" * 64)
    print()
    print("If you see 'Error 400: invalid_request / Missing client_id',")
    print("it means the URL above is being truncated by your terminal.")
    print("Copy it carefully — it must include client_id=...")


if __name__ == "__main__":
    main()
