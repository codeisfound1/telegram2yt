#!/usr/bin/env python3
"""
generate_token.py — One-time OAuth2 flow to create yt_token.json.

Works in GitHub Codespaces, remote SSH, and local machines.

Usage:
    python generate_token.py
    python generate_token.py --secrets path/to/client_secrets.json
    python generate_token.py --token-out my_token.json
    python generate_token.py --port 8080
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube OAuth token.")
    parser.add_argument(
        "--secrets",
        default="client_secrets.json",
        help="Path to client_secrets.json (default: client_secrets.json)",
    )
    parser.add_argument(
        "--token-out",
        default="yt_token.json",
        help="Where to save the token (default: yt_token.json)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Local port for OAuth redirect (default: 8080)",
    )
    args = parser.parse_args()

    secrets_path = Path(args.secrets)
    token_path = Path(args.token_out)
    PORT = args.port

    if not secrets_path.exists():
        print(f"ERROR: {secrets_path} not found.")
        print("Download it from:")
        print("  Google Cloud Console -> APIs & Services -> Credentials -> OAuth 2.0 Client ID")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: google-auth-oauthlib not installed.")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    # ------------------------------------------------------------------
    # Pre-flight checklist
    # ------------------------------------------------------------------
    print("=" * 64)
    print(" YouTube OAuth Token Generator")
    print("=" * 64)
    print()
    print("Before continuing, complete these steps in Google Cloud Console:")
    print()
    print(f"  STEP 1 — Add this Authorized Redirect URI to your OAuth client:")
    print(f"           http://localhost:{PORT}/")
    print()
    print("    Cloud Console -> APIs & Services -> Credentials")
    print("    -> Edit your Desktop OAuth 2.0 Client -> Authorized redirect URIs")
    print("    -> + Add URI -> http://localhost:{PORT}/ -> Save".format(PORT=PORT))
    print()
    print("  STEP 2 — Add your Google account as a Test User (if app is in Testing):")
    print("    Cloud Console -> APIs & Services -> OAuth consent screen")
    print("    -> Test users -> + Add Users -> your-email@gmail.com")
    print()

    in_codespaces = "CODESPACE_NAME" in os.environ
    if in_codespaces:
        print("  STEP 3 — [Codespaces] Forward the port:")
        print(f"    VS Code bottom panel -> Ports tab -> Add Port -> {PORT}")
        print(f"    Right-click {PORT} -> Port Visibility -> Public")
        print()
        print("  NOTE: After forwarding, the redirect URL Google sends back")
        print("  will still be http://localhost:{PORT}/ — that is correct.".format(PORT=PORT))
        print("  Codespaces intercepts localhost and tunnels it automatically.")
        print()

    input("Press Enter once the redirect URI is saved in Google Cloud Console...")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)

    print(f"Starting local OAuth server on port {PORT}...")
    print("Open the URL below in your browser:")
    print()

    creds = flow.run_local_server(
        host="0.0.0.0",        # bind all interfaces so Codespaces proxy can reach it
        port=PORT,
        open_browser=False,    # no desktop inside a container
        authorization_prompt_message=">>> Auth URL:\n{url}\n",
        success_message="Auth complete — you can close this tab and return to the terminal.",
    )

    token_path.write_text(creds.to_json())
    print()
    print(f"Token saved -> {token_path}")
    print()
    print("Next — encode it for GitHub Secrets:")
    print()
    print("  Linux / Codespaces:  base64 -w 0 yt_token.json")
    print("  macOS:               base64 -i yt_token.json")
    print()
    print("Paste the output as the YT_TOKEN_B64 GitHub Secret.")


if __name__ == "__main__":
    main()
