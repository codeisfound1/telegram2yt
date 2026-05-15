#!/usr/bin/env python3
“””
generate_token.py — One-time OAuth2 flow to create yt_token.json.

Run this locally BEFORE setting up CI. It opens a browser for Google
authorisation and saves the token to yt_token.json.

Usage:
python generate_token.py
python generate_token.py –secrets path/to/client_secrets.json
python generate_token.py –token-out my_token.json
“””

import argparse
import sys
from pathlib import Path

def main():
parser = argparse.ArgumentParser(description=“Generate YouTube OAuth token.”)
parser.add_argument(
“–secrets”,
default=“client_secrets.json”,
help=“Path to client_secrets.json (default: client_secrets.json)”,
)
parser.add_argument(
“–token-out”,
default=“yt_token.json”,
help=“Where to save the token (default: yt_token.json)”,
)
args = parser.parse_args()

```
secrets_path = Path(args.secrets)
token_path = Path(args.token_out)

if not secrets_path.exists():
    print(f"ERROR: {secrets_path} not found.")
    print("Download it from: Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client")
    sys.exit(1)

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERROR: google-auth-oauthlib not installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

print(f"Loading secrets from: {secrets_path}")
print("A browser window will open. Log in and grant YouTube upload access.")
print()

flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
creds = flow.run_local_server(port=0, open_browser=True)

token_path.write_text(creds.to_json())
print()
print(f"Token saved to: {token_path}")
print()
print("Next step — encode it for GitHub Secrets:")
print()
print("  Linux/WSL:  base64 -w 0 yt_token.json")
print("  macOS:      base64 -i yt_token.json")
print()
print("Paste the output as the YT_TOKEN_B64 GitHub Secret.")
```

if **name** == “**main**”:
main()
