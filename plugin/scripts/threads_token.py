"""Exchange Threads OAuth code for a long-lived token.

Usage:
    # Step 1: Open the auth URL printed by this script
    python3 threads_token.py --app-id YOUR_APP_ID --app-secret YOUR_APP_SECRET --redirect-uri https://localhost/

    # Step 2: After authorizing, copy the 'code' param from the redirect URL
    python3 threads_token.py --app-id YOUR_APP_ID --app-secret YOUR_APP_SECRET --redirect-uri https://localhost/ --code THE_CODE
"""

import argparse
import requests
import sys

THREADS_GRAPH = "https://graph.threads.net"


def get_auth_url(app_id, redirect_uri):
    scopes = "threads_basic,threads_content_publish,threads_manage_replies,threads_read_replies"
    return (
        f"https://threads.net/oauth/authorize"
        f"?client_id={app_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scopes}"
        f"&response_type=code"
    )


def exchange_code_for_short_token(app_id, app_secret, redirect_uri, code):
    """Step 2: Exchange authorization code for short-lived token."""
    resp = requests.post(
        f"{THREADS_GRAPH}/oauth/access_token",
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        },
    )
    data = resp.json()
    if "access_token" not in data:
        print(f"ERROR getting short-lived token: {data}")
        sys.exit(1)
    return data["access_token"]


def exchange_for_long_lived(app_secret, short_token):
    """Step 3: Exchange short-lived token for long-lived token (60 days)."""
    resp = requests.get(
        f"{THREADS_GRAPH}/access_token",
        params={
            "grant_type": "th_exchange_token",
            "client_secret": app_secret,
            "access_token": short_token,
        },
    )
    data = resp.json()
    if "access_token" not in data:
        print(f"ERROR getting long-lived token: {data}")
        sys.exit(1)
    return data["access_token"], data.get("expires_in")


def main():
    parser = argparse.ArgumentParser(description="Get Threads long-lived token via OAuth")
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--app-secret", required=True)
    parser.add_argument("--redirect-uri", required=True)
    parser.add_argument("--code", help="Authorization code from redirect URL")
    args = parser.parse_args()

    if not args.code:
        url = get_auth_url(args.app_id, args.redirect_uri)
        print("=" * 60)
        print("Step 1: Open this URL in your browser and authorize:")
        print()
        print(url)
        print()
        print("Step 2: After authorizing, you'll be redirected to:")
        print(f"  {args.redirect_uri}?code=XXXXXX#_")
        print()
        print("Step 3: Copy the 'code' value and re-run:")
        print(f'  python3 {sys.argv[0]} --app-id {args.app_id} --app-secret {args.app_secret} --redirect-uri {args.redirect_uri} --code PASTE_CODE_HERE')
        print("=" * 60)
        return

    print("Exchanging code for short-lived token...")
    short_token = exchange_code_for_short_token(args.app_id, args.app_secret, args.redirect_uri, args.code)
    print(f"Short-lived token: {short_token[:20]}...")

    print("Exchanging for long-lived token...")
    long_token, expires_in = exchange_for_long_lived(args.app_secret, short_token)

    days = expires_in // 86400 if expires_in else "?"
    print()
    print("=" * 60)
    print("LONG-LIVED TOKEN (copy this):")
    print()
    print(long_token)
    print()
    print(f"Expires in: {days} days")
    print("=" * 60)


if __name__ == "__main__":
    main()
