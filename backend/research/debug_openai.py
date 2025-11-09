"""Simple debug script to understand OpenAI Responses API structure."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env from {env_path}\n")

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env")

client = OpenAI(api_key=api_key)

# Simple test query
print("Testing OpenAI Responses API with web_search...\n")

response = client.responses.create(
    model="gpt-5-mini",
    tools=[{"type": "web_search"}],
    input="When is the next iPhone being released?",
    include=["web_search_call.action.sources"],
)

print("=" * 80)
print("FULL RESPONSE STRUCTURE")
print("=" * 80)
print(f"\nResponse type: {type(response)}")
print(f"\nResponse attributes: {dir(response)}")

# Print response as dict if possible
if hasattr(response, "model_dump"):
    print("\n" + "=" * 80)
    print("RESPONSE AS DICT (model_dump)")
    print("=" * 80)
    response_dict = response.model_dump()
    print(json.dumps(response_dict, indent=2, default=str))
elif hasattr(response, "to_dict"):
    print("\n" + "=" * 80)
    print("RESPONSE AS DICT (to_dict)")
    print("=" * 80)
    print(json.dumps(response.to_dict(), indent=2, default=str))

# Examine usage
print("\n" + "=" * 80)
print("USAGE INFORMATION")
print("=" * 80)
if hasattr(response, "usage"):
    print(f"Usage type: {type(response.usage)}")
    print(f"Usage attributes: {dir(response.usage)}")
    if hasattr(response.usage, "model_dump"):
        print(f"Usage dict: {json.dumps(response.usage.model_dump(), indent=2)}")

# Examine output
print("\n" + "=" * 80)
print("OUTPUT STRUCTURE")
print("=" * 80)
if hasattr(response, "output"):
    print(f"Output type: {type(response.output)}")
    print(
        f"Output length: {len(response.output) if hasattr(response.output, '__len__') else 'N/A'}"
    )

    for i, item in enumerate(response.output):
        print(f"\n--- Output Item {i} ---")
        print(f"Type: {item.type}")
        print(f"Attributes: {dir(item)}")

        if item.type == "web_search_call":
            print(f"\nweb_search_call attributes: {dir(item)}")
            if hasattr(item, "action"):
                print(f"Action type: {type(item.action)}")
                print(f"Action attributes: {dir(item.action)}")
                if hasattr(item.action, "sources"):
                    print(f"\nSources type: {type(item.action.sources)}")
                    print(f"Sources length: {len(item.action.sources)}")
                    if item.action.sources:
                        source = item.action.sources[0]
                        print(f"\nFirst source type: {type(source)}")
                        print(f"First source attributes: {dir(source)}")
                        if hasattr(source, "model_dump"):
                            print(f"First source dict: {json.dumps(source.model_dump(), indent=2)}")

        elif item.type == "message":
            print(f"\nMessage attributes: {dir(item)}")
            if hasattr(item, "content"):
                print(f"Content type: {type(item.content)}")
                if hasattr(item.content, "__iter__"):
                    for j, content_item in enumerate(item.content):
                        print(f"\n  Content item {j} type: {type(content_item)}")
                        print(f"  Content item {j} attributes: {dir(content_item)}")
                        if hasattr(content_item, "annotations"):
                            print(f"  Annotations: {content_item.annotations}")

# Get output text
print("\n" + "=" * 80)
print("OUTPUT TEXT")
print("=" * 80)
if hasattr(response, "output_text"):
    print(response.output_text)

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
