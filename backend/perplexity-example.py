import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

url = "https://api.perplexity.ai/chat/completions"
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

if not perplexity_api_key:
    raise ValueError(
        "PERPLEXITY_API_KEY not found in .env file or environment variables"
    )

headers = {
    "Authorization": f"Bearer {perplexity_api_key}",
    "Content-Type": "application/json",
}

initial_user_query = "discounts in tkmax"
print(f"Initial User Query: {initial_user_query}\n")

# --- Step 1: Generate Intermediate Query ---
system_prompt_step1 = """You are an AI assistant that refines a user's general interest into a focused search query.
The user wants to monitor a topic, entity, or type of information online for any significant changes or new updates.
Your task is to transform their initial interest into a concise search query string. This refined query should be designed to help another AI find one or more stable, central webpages (e.g., official news sections, main product/service pages, primary blog URLs, key community hubs, or official announcement channels) that are most likely to be updated when new, relevant information appears.
Output *only* the refined search query string. No explanations or labels.

Example User Interest: "latest from OpenAI"
Example Refined Query Output: "OpenAI official announcements or blog"

Example User Interest: "Sony camera rumors"
Example Refined Query Output: "Sony camera news and rumor hubs"

Example User Interest: "discounts in tkmaxx"
Example Refined Query Output: "TK Maxx official offers and deals page"""

payload_step1 = {
    "model": "sonar",
    "messages": [
        {"role": "system", "content": system_prompt_step1},
        {"role": "user", "content": initial_user_query},
    ],
}

print("--- Running Step 1: Generate Intermediate Query ---")
response_step1 = requests.request("POST", url, json=payload_step1, headers=headers)
response_step1_data = response_step1.json()

intermediate_query = ""
if response_step1_data.get("choices") and len(response_step1_data["choices"]) > 0:
    intermediate_query = response_step1_data["choices"][0]["message"]["content"].strip()
    print(f"Generated Intermediate Query: {intermediate_query}\n")
else:
    print("Error: Could not generate intermediate query from Step 1.")
    print(f"Step 1 Response: {json.dumps(response_step1_data, indent=2)}")
    exit()

if not intermediate_query:
    print("Error: Intermediate query is empty.")
    exit()

# --- Step 2: Find Monitorable Website using Intermediate Query ---
system_prompt_step2 = """Based on the user's search query, which expresses an interest in monitoring a topic for updates:
1. Identify one or more primary, stable URLs that are central to the user's interest and likely to be updated when relevant new information, products, services, news, or offers appear.
2. Prioritize official pages (e.g., news sections, main product/service category homepages, primary blog URLs, official offer/announcement channels) or highly reputable and comprehensive community hubs/forums if appropriate for the topic (e.g., for discussions, rumors, or community-driven updates).
3. The goal is to find pages that serve as ongoing, canonical sources of information or updates for the given query, suitable for long-term monitoring.
4. Avoid linking to specific, transient articles or individual forum posts unless they are explicitly designed as continuously updated 'live blogs' or master threads.
5. Output a list of these relevant URLs, each on a new line.
6. Output *only* the list of URLs. No extra text, explanations, or numbering.

Example User Query: "OpenAI official announcements or blog"
Example Expected Output:
openai.com/blog
openai.com/news

Example User Query: "Sony camera news and rumor hubs"
Example Expected Output:
sonyalpharumors.com
dpreview.com/news/sony

Example User Query: "TK Maxx official offers and deals page"
Example Expected Output:
tkmaxx.com/uk/en/offers
"""

payload_step2 = {
    "model": "sonar",
    "messages": [
        {"role": "system", "content": system_prompt_step2},
        {"role": "user", "content": intermediate_query},
    ],
}

print("--- Running Step 2: Find Monitorable Website(s) ---")
response_step2 = requests.request("POST", url, json=payload_step2, headers=headers)
response_step2_data = response_step2.json()

monitorable_urls = []
if response_step2_data.get("choices") and len(response_step2_data["choices"]) > 0:
    content = response_step2_data["choices"][0]["message"]["content"].strip()
    if content:
        monitorable_urls = [url.strip() for url in content.split("\n") if url.strip()]

    if monitorable_urls:
        print(f"Identified Monitorable URL(s):\n")
        for url_item in monitorable_urls:
            print(url_item)
        print("")
    else:
        print(
            "No monitorable URLs identified in Step 2 content, or content was empty.\n"
        )
elif not intermediate_query:
    print("Error: Intermediate query is empty. Skipping Step 2.")
else:
    print(
        "Error: Could not identify monitorable URL(s) from Step 2 response structure."
    )
    print(f"Step 2 Response (choices): {response_step2_data.get('choices')}\n")


if "citations" in response_step2_data:
    print("Citations from Step 2:")
    for citation in response_step2_data["citations"]:
        print(citation)
else:
    print("No citations found in Step 2.")

# # For debugging Step 1 full response
# print("\nFull Step 1 response JSON:")
# print(json.dumps(response_step1_data, indent=2))

# # For debugging Step 2 full response
# print("\nFull Step 2 response JSON:")
# print(json.dumps(response_step2_data, indent=2))
