"""Quick test script for TwitterAPI.io endpoints."""

import asyncio
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.twitterapi.io"
API_KEY = os.environ["TWITTERIO_API_KEY"]
HEADERS = {"X-API-Key": API_KEY}

DELAY = 6  # free tier: 1 req per 5s


def _parse(resp: httpx.Response) -> dict:
    """Check status and parse JSON, printing errors gracefully."""
    print(f"Status: {resp.status_code}")
    try:
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPStatusError, json.JSONDecodeError):
        print(f"API call failed. Response: {resp.text[:500]}")
        return {}


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS, timeout=15) as client:
        # 1. Advanced tweet search
        print("=== Tweet Advanced Search ===")
        resp = await client.get(
            "/twitter/tweet/advanced_search",
            params={"query": "python programming", "queryType": "Latest"},
        )
        data = _parse(resp)
        for t in data.get("tweets", [])[:3]:
            author = t.get("author", {})
            print(f"  @{author.get('userName', '?')}: {t.get('text', '')[:100]}")

        await asyncio.sleep(DELAY)

        # 2. Get user profile
        print("\n=== User Profile ===")
        resp = await client.get("/twitter/user/info", params={"userName": "elonmusk"})
        data = _parse(resp)
        user = data.get("data", {})
        if user:
            print(f"Name: {user.get('name')}, Followers: {user.get('followers')}")

        await asyncio.sleep(DELAY)

        # 3. User tweets
        print("\n=== User Tweets ===")
        resp = await client.get(
            "/twitter/user/last_tweets",
            params={"userName": "OpenAI", "limit": "3"},
        )
        data = _parse(resp)
        for t in data.get("tweets", [])[:3]:
            print(f"  {t.get('text', '')[:120]}")


if __name__ == "__main__":
    asyncio.run(main())
