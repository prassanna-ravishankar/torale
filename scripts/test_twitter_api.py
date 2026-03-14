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


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS, timeout=15) as client:
        # 1. Advanced tweet search
        print("=== Tweet Advanced Search ===")
        resp = await client.get(
            "/twitter/tweet/advanced_search",
            params={"query": "python programming", "queryType": "Latest"},
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        tweets = data.get("tweets", [])
        for t in tweets[:3]:
            author = t.get("author", {})
            print(f"  @{author.get('userName', '?')}: {t.get('text', '')[:100]}")
        if not tweets:
            print(json.dumps(data, indent=2)[:500])

        await asyncio.sleep(DELAY)

        # 2. Get user profile
        print("\n=== User Profile ===")
        resp = await client.get("/twitter/user/info", params={"userName": "elonmusk"})
        print(f"Status: {resp.status_code}")
        data = resp.json()
        user = data.get("data", {})
        if user:
            print(f"Name: {user.get('name')}, Followers: {user.get('followers')}")
        else:
            print(json.dumps(data, indent=2)[:500])

        await asyncio.sleep(DELAY)

        # 3. User tweets
        print("\n=== User Tweets ===")
        resp = await client.get(
            "/twitter/user/last_tweets",
            params={"userName": "OpenAI", "limit": "3"},
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        tweets = data.get("tweets", [])
        for t in tweets[:3]:
            print(f"  {t.get('text', '')[:120]}")
        if not tweets:
            print(json.dumps(data, indent=2)[:500])


if __name__ == "__main__":
    asyncio.run(main())
