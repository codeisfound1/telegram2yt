#!/usr/bin/env python3
"""
generate_token.py — Creates yt_token.json using Google OAuth Playground.

No local server. No redirect issues. Works in Codespaces, SSH, anywhere.

Usage:
    python generate_token.py
    python generate_token.py --secrets client_secrets.json
    python generate_token.py --token-out yt_token.json
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets", default="client_secrets.json")
    parser.add_argument("--token-out", default="yt_token.json")
    args = parser.parse_args()

    secrets_path = Path(args.secrets)
    token_path   = Path(args.token_out)

    # ------------------------------------------------------------------
    # Load client credentials
    # ------------------------------------------------------------------
    if not secrets_path.exists():
        print(f"ERROR: {secrets_path} not found.")
        sys.exit(1)

    raw         = json.loads(secrets_path.read_text())
    client_info = raw.get("installed") or raw.get("web")
    if not client_info:
        print("ERROR: client_secrets.json has unexpected format.")
        sys.exit(1)

    client_id     = client_info["client_id"]
    client_secret = client_info["client_secret"]
    token_uri     = client_info.get("token_uri", "https://oauth2.googleapis.com/token")

    # ------------------------------------------------------------------
    # Instructions
    # ------------------------------------------------------------------
    print()
    print("=" * 64)
    print("  YouTube Token Generator — via OAuth Playground")
    print("=" * 64)
    print()
    print("This flow uses https://developers.google.com/oauthplayground")
    print("No redirect URI setup needed. Works anywhere.")
    print()
    print("STEP 1 — Configure the Playground with YOUR app credentials:")
    print()
    print("  a) Open: https://developers.google.com/oauthplayground")
    print("  b) Click the gear icon (top-right) -> check:")
    print('     [x] "Use your own OAuth credentials"')
    print(f"  c) OAuth Client ID:     {client_id}")
    print(f"  d) OAuth Client secret: {client_secret}")
    print("  e) Close the gear panel.")
    print()
    print("STEP 2 — Authorize the YouTube scope:")
    print()
    print("  a) In the left panel, scroll to 'YouTube Data API v3'")
    print("     OR paste this into the scope box:")
    print("     https://www.googleapis.com/auth/youtube.upload")
    print("  b) Click 'Authorize APIs' -> choose your Google account.")
    print()
    print("STEP 3 — Exchange for tokens:")
    print()
    print("  a) Click 'Exchange authorization code for tokens'.")
    print("  b) Copy the value shown in the 'Refresh token' field.")
    print()
    print("-" * 64)
    print()

    refresh_token = input("Paste your Refresh token here: ").strip()
    if not refresh_token:
        print("ERROR: No token entered.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Verify the refresh token works by fetching an access token
    # ------------------------------------------------------------------
    print()
    print("Verifying token...")

    try:
        import requests
    except ImportError:
        print("ERROR: requests not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    resp = requests.post(token_uri, data={
        "client_id":     client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type":    "refresh_token",
    }, timeout=30)

    if not resp.ok:
        print(f"ERROR: Could not verify token ({resp.status_code}):")
        print(resp.text)
        sys.exit(1)

    access_token = resp.json().get("access_token", "")
    print("Token verified OK.")

    # ------------------------------------------------------------------
    # Save in google-auth compatible format
    # ------------------------------------------------------------------
    creds_json = {
        "token":         access_token,
        "refresh_token": refresh_token,
        "token_uri":     token_uri,
        "client_id":     client_id,
        "client_secret": client_secret,
        "scopes":        ["https://www.googleapis.com/auth/youtube.upload"],
    }

    token_path.write_text(json.dumps(creds_json, indent=2))

    print(f"Token saved -> {token_path}")
    print()
    print("Next — encode for GitHub Secrets:")
    print()
    print("  Linux / Codespaces:  base64 -w 0 yt_token.json")
    print("  macOS:               base64 -i yt_token.json")
    print()
    print("Paste the result as the YT_TOKEN_B64 GitHub Secret.")


if __name__ == "__main__":
    main()
