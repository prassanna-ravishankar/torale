#!/usr/bin/env python
"""Simple test script for the discovery service"""

import asyncio
import aiohttp
import sys


async def test_discovery_service():
    """Test the discovery service endpoints"""
    base_url = "http://localhost:8001"
    
    # Test health check
    print("Testing health check...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Health check passed: {data}")
                else:
                    print(f"✗ Health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"✗ Failed to connect to service: {e}")
            print("Make sure the discovery service is running on port 8001")
            return
    
    # Test discovery endpoint
    print("\nTesting discovery endpoint...")
    test_queries = [
        "latest updates from OpenAI",
        "Tesla stock price changes",
        "AWS service announcements",
        "Python programming tutorials"
    ]
    
    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            try:
                payload = {"raw_query": query}
                async with session.post(
                    f"{base_url}/api/v1/discover",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        urls = data.get("monitorable_urls", [])
                        print(f"✓ Found {len(urls)} sources:")
                        for url in urls:
                            print(f"  - {url}")
                    else:
                        error = await response.text()
                        print(f"✗ Discovery failed: {response.status} - {error}")
            except Exception as e:
                print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("Discovery Service Test\n" + "=" * 50)
    asyncio.run(test_discovery_service())