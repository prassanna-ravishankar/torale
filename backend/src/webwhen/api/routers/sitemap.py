"""SEO endpoints: changelog RSS + robots.txt.

The sitemap (`/sitemap.xml`) is owned by the Next.js frontend via its
native `app/sitemap.ts` convention — it has direct access to PUBLIC_ROUTES
and the same `/api/v1/public/tasks` endpoint this service exposes. The
backend used to serve a sitemap-index pointing at a frontend-static and
backend-dynamic split; that distinction is gone now and the Gateway
HTTPRoute routes `/sitemap.xml` to the frontend.

The changelog RSS (`/changelog.xml`) stays here because it's a different
content type (application/rss+xml, not application/xml-sitemap) read by
feed clients, not crawlers, and the source-of-truth changelog.json lives
in this repo and is read by the backend.

`robots.txt` stays here for two reasons: (1) it needs the host-discrimination
logic to disallow the api host wholesale (SEO audit V2 B4), and (2) the
Gateway already routes `/robots.txt` to the backend service.
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request, Response

from webwhen.core.config import PROJECT_ROOT, settings

# Register atom namespace once at module level (avoids per-request global mutation)
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")

router = APIRouter(tags=["seo"])


def _is_marketing_host(request: Request) -> bool:
    """
    True when the inbound request hits the marketing-zone hostname (the host
    component of settings.frontend_url).

    The same FastAPI app serves both marketing-routed paths via Gateway
    HTTPRoute (/robots.txt, /changelog.xml on webwhen.ai) and the API zone
    (api.webwhen.ai). The k8s HTTPRoute for api.webwhen.ai forwards every
    path to this app, so these endpoints on the api host would otherwise
    mirror the marketing surface — confusing for crawlers and a cross-host
    declaration anti-pattern. SEO audit V2 (B4).

    Falls back to True when request.url.hostname is unavailable (test client
    edge cases) so existing tests and unauthenticated localhost dev don't
    regress.
    """
    request_host = request.url.hostname
    if not request_host:
        return True
    marketing_host = urlparse(settings.frontend_url).hostname
    return request_host == marketing_host


@router.get("/changelog.xml")
async def generate_changelog_rss(request: Request):
    """
    Generate RSS 2.0 feed for changelog.

    Reads changelog.json from frontend/public and converts to RSS format.
    Includes first 50 entries with proper RFC-2822 date formatting.
    """
    if not _is_marketing_host(request):
        raise HTTPException(status_code=404)

    # Get changelog path from settings (supports both relative and absolute paths)
    changelog_path = Path(settings.changelog_json_path)
    if not changelog_path.is_absolute():
        changelog_path = PROJECT_ROOT / changelog_path

    if not changelog_path.exists():
        raise FileNotFoundError(f"Changelog file not found at configured path: {changelog_path}")

    # Read and parse changelog
    with open(changelog_path, encoding="utf-8") as f:
        entries = json.load(f)

    # Take first MAX_RSS_ENTRIES entries
    MAX_RSS_ENTRIES = 50
    entries = entries[:MAX_RSS_ENTRIES]

    base_url = settings.frontend_url

    # Create RSS structure
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "webwhen changelog"
    ET.SubElement(channel, "link").text = f"{base_url}/changelog"
    ET.SubElement(
        channel, "description"
    ).text = "Updates to webwhen — the agent that waits for the web."
    ET.SubElement(channel, "language").text = "en-us"

    # Add atom:link for feed autodiscovery
    atom_link = ET.SubElement(
        channel, "{http://www.w3.org/2005/Atom}link", rel="self", type="application/rss+xml"
    )
    atom_link.set("href", f"{base_url}/changelog.xml")

    # Convert entries to RSS items
    for entry in entries:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = entry["title"]
        ET.SubElement(item, "link").text = f"{base_url}/changelog#{entry['id']}"
        ET.SubElement(item, "guid", isPermaLink="true").text = f"{base_url}/changelog#{entry['id']}"

        # Convert date from "2026-02-11" to RFC-2822 format
        date_obj = datetime.strptime(entry["date"], "%Y-%m-%d")
        pub_date = format_datetime(date_obj)
        ET.SubElement(item, "pubDate").text = pub_date

        # Add description (XML-escaped by ElementTree)
        description = ET.SubElement(item, "description")
        description.text = entry["description"]

        # Add category
        category_map = {
            "feature": "New Feature",
            "improvement": "Improvement",
            "infra": "Infrastructure",
            "research": "Research",
        }
        category_text = category_map.get(entry["category"], entry["category"].title())
        ET.SubElement(item, "category").text = category_text

    # Convert to XML with declaration
    xml_output = ET.tostring(rss, encoding="utf-8", xml_declaration=True)

    return Response(content=xml_output, media_type="application/rss+xml")


PROD_FRONTEND_URLS = frozenset({"https://webwhen.ai", "https://torale.ai"})


@router.get("/robots.txt")
async def robots_txt(request: Request):
    """
    robots.txt for search engine crawlers. Non-prod hosts and the API host
    return a blanket disallow so staging/preview deployments and api.webwhen.ai
    don't get indexed (api host has no public web pages — see B4).
    """
    base_url = settings.frontend_url

    if not _is_marketing_host(request):
        return Response(content="User-agent: *\nDisallow: /\n", media_type="text/plain")

    if base_url not in PROD_FRONTEND_URLS:
        return Response(content="User-agent: *\nDisallow: /\n", media_type="text/plain")

    # Disallow covers both live hyphenated routes (/sign-in, /sign-up) and
    # the legacy un-hyphenated forms (/signin, /signup) so historical inbound
    # links remain covered. /admin and /admin/ both listed because /admin/
    # only matches /admin/foo, not /admin exact. /dashboard and /welcome
    # added — auth-gated SPA routes that should not be indexed. /tasks/ stays
    # Allow (covers public task pages enumerated in the frontend sitemap).
    robots = f"""User-agent: *
Allow: /
Allow: /explore
Allow: /tasks/

Disallow: /api/
Disallow: /auth/
Disallow: /signin
Disallow: /sign-in
Disallow: /signup
Disallow: /sign-up
Disallow: /settings
Disallow: /admin
Disallow: /admin/
Disallow: /dashboard
Disallow: /welcome

Sitemap: {base_url}/sitemap.xml
"""

    return Response(content=robots, media_type="text/plain")
