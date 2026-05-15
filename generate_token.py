#!/usr/bin/env python3
"""
generate_token.py — One-time OAuth2 flow to create yt_token.json.

Works in GitHub Codespaces, remote SSH, WSL, and local machines.
Uses a manual copy-paste flow that avoids all redirect/state issues.

Usage:
    python generate_token.py
    python generate_token.py --secrets path/to/client_secrets.json
    python generate_token.py --token-out my_token.json
"""

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube OAuth token.")
    parser.add_argument("--secrets", default="client_secrets.json")
    parser.add_argument("--token-out", default="yt_token.json")
    args = parser.parse_args()

    secrets_path = Path(args.secrets)
    token_path = Path(args.token_out)

    if not secrets_path.exists():
        print(f"ERROR: {secrets_path} not found.")
        print("Download it from Google Cloud Console -> APIs & Services -> Credentials")
        sys.exit(1)

    try:
        import requests
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        print("ERROR: Missing dependencies. Run: pip install -r requirements.txt")
        sys.exit(1)

    # Load client secrets
    raw = json.loads(secrets_path.read_text())
    # Supports both "installed" and "web" client types
    client_info = raw.get("installed") or raw.get("web")
    if not client_info:
        print("ERROR: client_secrets.json has unexpected format.")
        sys.exit(1)

    client_id     = client_info["client_id"]
    client_secret = client_info["client_secret"]
    token_uri     = client_info.get("token_uri", "https://oauth2.googleapis.com/token")

    SCOPE         = "https://www.googleapis.com/auth/youtube.upload"
    # This redirect URI must be added to your OAuth client in Google Cloud Console
    REDIRECT_URI  = "http://localhost"

    # ------------------------------------------------------------------
    # Step 1 — build the auth URL manually (no local server needed)
    # ------------------------------------------------------------------
    params = {
        "client_id":     client_id,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPE,
        "access_type":   "offline",
        "prompt":        "consent",   # ensures refresh_token is returned
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    print("=" * 64)
    print(" YouTube OAuth Token Generator")
    print("=" * 64)
    print()
    print("PREREQUISITE — add this Redirect URI to your Google OAuth client:")
    print()
    print("    http://localhost")
    print()
    print("  Cloud Console -> APIs & Services -> Credentials")
    print("  -> Edit your Desktop OAuth 2.0 Client")
    print("  -> Authorized redirect URIs -> + Add URI -> http://localhost")
    print("  -> Save")
    print()
    print("Also make sure your Google account is listed as a Test User if")
    print("the OAuth consent screen is still in 'Testing' mode.")
    print()
    print("-" * 64)
    print()
    print("STEP 1 — Open this URL in your browser:")
    print()
    print(auth_url)
    print()
    print("-" * 64)
    print()
    print("STEP 2 — After approving, the browser will redirect to a URL")
    print("that looks like:  http://localhost/?code=4/0Ab...&scope=...")
    print()
    print("The page will show 'This site can't be reached' — that is fine.")
    print("Copy the ENTIRE URL from the browser address bar and paste below.")
    print()

    redirected = input("Paste the full redirect URL here: ").strip()

    # Extract the code from the pasted URL
    parsed = urllib.parse.urlparse(redirected)
    qs = urllib.parse.parse_qs(parsed.query)

    if "error" in qs:
        print(f"\nERROR from Google: {qs['error']}")
        sys.exit(1)

    if "code" not in qs:
        # Maybe they pasted just the code, not the full URL
        code = redirected.strip()
        if not code:
            print("\nERROR: No code found in the URL. Did you paste the full address bar URL?")
            sys.exit(1)
    else:
        code = qs["code"][0]

    # ------------------------------------------------------------------
    # Step 2 — exchange code for tokens
    # ------------------------------------------------------------------
    print("\nExchanging code for tokens...")

    resp = requests.post(token_uri, data={
        "code":          code,
        "client_id":     client_id,
        "client_secret": client_secret,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    }, timeout=30)

    if not resp.ok:
        print(f"ERROR: Token exchange failed ({resp.status_code}): {resp.text}")
        sys.exit(1)

    token_data = resp.json()

    if "refresh_token" not in token_data:
        print("WARNING: No refresh_token in response.")
        print("This usually means the account already granted access.")
        print("Revoke access at https://myaccount.google.com/permissions and re-run.")

    # ------------------------------------------------------------------
    # Step 3 — save as google-auth compatible JSON
    # ------------------------------------------------------------------
    creds_json = {
        "token":         token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "token_uri":     token_uri,
        "client_id":     client_id,
        "client_secret": client_secret,
        "scopes":        [SCOPE],
    }

    token_path.write_text(json.dumps(creds_json, indent=2))

    print(f"\nToken saved -> {token_path}")
    print()
    print("Next — encode it for GitHub Secrets:")
    print()
    print("  Linux / Codespaces:  base64 -w 0 yt_token.json")
    print("  macOS:               base64 -i yt_token.json")
    print()
    print("Paste the output as the YT_TOKEN_B64 GitHub Secret.")


if __name__ == "__main__":
    main()
