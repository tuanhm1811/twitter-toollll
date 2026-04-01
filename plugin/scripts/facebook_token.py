"""Exchange a short-lived Facebook User Token for a long-lived Page Access Token.

Usage:
    # Step 1: Get a short-lived user token from Graph API Explorer
    #   -> https://developers.facebook.com/tools/explorer/
    #   -> Select your app, add pages_manage_posts + pages_read_engagement permissions
    #   -> Click "Generate Access Token" and authorize

    # Step 2: Run this script with the short-lived token
    python3 facebook_token.py \
        --app-id YOUR_APP_ID \
        --app-secret YOUR_APP_SECRET \
        --short-token THE_SHORT_LIVED_TOKEN \
        --page-id YOUR_PAGE_ID
"""

import argparse
import requests
import sys

GRAPH_API = "https://graph.facebook.com/v19.0"


def exchange_for_long_lived_user_token(app_id, app_secret, short_token):
    """Exchange short-lived user token for long-lived user token (60 days)."""
    resp = requests.get(
        f"{GRAPH_API}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token,
        },
    )
    data = resp.json()
    if "access_token" not in data:
        print(f"ERROR: {data.get('error', {}).get('message', data)}")
        sys.exit(1)
    return data["access_token"], data.get("expires_in")


def get_page_access_token(user_token, page_id):
    """Get a never-expiring Page Access Token from a long-lived user token."""
    resp = requests.get(
        f"{GRAPH_API}/{page_id}",
        params={
            "fields": "access_token",
            "access_token": user_token,
        },
    )
    data = resp.json()
    if "access_token" not in data:
        print(f"ERROR getting page token: {data.get('error', {}).get('message', data)}")
        sys.exit(1)
    return data["access_token"]


def main():
    parser = argparse.ArgumentParser(description="Get long-lived Facebook Page Access Token")
    parser.add_argument("--app-id", required=True, help="Facebook App ID")
    parser.add_argument("--app-secret", required=True, help="Facebook App Secret")
    parser.add_argument("--short-token", required=True, help="Short-lived user token from Graph API Explorer")
    parser.add_argument("--page-id", required=True, help="Facebook Page ID")
    args = parser.parse_args()

    print("Step 1: Exchanging short-lived token for long-lived user token...")
    long_user_token, expires_in = exchange_for_long_lived_user_token(
        args.app_id, args.app_secret, args.short_token
    )
    days = expires_in // 86400 if expires_in else "?"
    print(f"  Long-lived user token obtained (expires in {days} days)")

    print(f"Step 2: Getting page access token for page {args.page_id}...")
    page_token = get_page_access_token(long_user_token, args.page_id)

    print()
    print("=" * 60)
    print("PAGE ACCESS TOKEN (never expires — copy this):")
    print()
    print(page_token)
    print()
    print("Update .social-agent.yaml:")
    print(f'  facebook.page_access_token: "{page_token}"')
    print("=" * 60)


if __name__ == "__main__":
    main()
