"""Sitemap generation for SEO."""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from webwhen.core.config import PROJECT_ROOT, settings
from webwhen.core.database import Database, get_db

# Register atom namespace once at module level (avoids per-request global mutation)
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")

router = APIRouter(tags=["seo"])


def _is_marketing_host(request: Request) -> bool:
    """
    True when the inbound request hits the marketing-zone hostname (the host
    component of settings.frontend_url).

    The same FastAPI app serves both marketing-routed paths via Gateway
    HTTPRoute (/sitemap.xml, /robots.txt, /changelog.xml on webwhen.ai) and
    the API zone (api.webwhen.ai). The k8s HTTPRoute for api.webwhen.ai
    forwards every path to this app, so /sitemap.xml on the api host would
    otherwise mirror the marketing sitemap — confusing for crawlers and a
    cross-host sitemap-declaration anti-pattern. SEO audit V2 (B4).

    Falls back to True when request.url.hostname is unavailable (test client
    edge cases) so existing tests and unauthenticated localhost dev don't
    regress.
    """
    request_host = request.url.hostname
    if not request_host:
        return True
    marketing_host = urlparse(settings.frontend_url).hostname
    return request_host == marketing_host


@router.get("/sitemap.xml")
async def generate_sitemap_index(request: Request, db: Database = Depends(get_db)):
    """
    Sitemap index pointing at the static (frontend-served) and dynamic (backend)
    child sitemaps. Frontend owns enumerated SEO routes (publicRoutes.ts);
    backend owns DB-derived public task pages.
    """
    if not _is_marketing_host(request):
        raise HTTPException(status_code=404)

    base_url = settings.frontend_url

    latest_task_lastmod = await db.fetch_val(
        "SELECT MAX(updated_at) FROM tasks WHERE is_public = true"
    )
    dynamic_lastmod = (
        latest_task_lastmod.strftime("%Y-%m-%d")
        if latest_task_lastmod
        else datetime.now().strftime("%Y-%m-%d")
    )
    static_lastmod = datetime.now().strftime("%Y-%m-%d")

    sitemapindex = ET.Element("sitemapindex", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for loc, lastmod in (
        (f"{base_url}/sitemap-static.xml", static_lastmod),
        (f"{base_url}/sitemap-dynamic.xml", dynamic_lastmod),
    ):
        sitemap_elem = ET.SubElement(sitemapindex, "sitemap")
        ET.SubElement(sitemap_elem, "loc").text = loc
        ET.SubElement(sitemap_elem, "lastmod").text = lastmod

    xml_output = ET.tostring(sitemapindex, encoding="utf-8", xml_declaration=True)
    return Response(content=xml_output, media_type="application/xml")


@router.get("/sitemap-dynamic.xml")
async def generate_sitemap_dynamic(request: Request, db: Database = Depends(get_db)):
    """
    Dynamic sitemap covering DB-derived public pages.

    `/` and `/changelog` carry DB-truth lastmod values (newest is_public task
    timestamp; newest changelog.json entry). `/explore` and `/tasks/<UUID>`
    re-added once the Next.js migration made them genuinely server-rendered:
    Googlebot now gets real HTML for those URLs, so submitting them in the
    sitemap promises content that actually exists. (They were removed in SEO
    audit V2 (B3) when the Vite SPA shipped empty shells to non-JS crawlers.)

    Per-task lastmod uses the watch's updated_at so deploys don't churn every
    task's "last modified" in Google Search Console.
    """
    if not _is_marketing_host(request):
        raise HTTPException(status_code=404)

    base_url = settings.frontend_url

    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Landing-page lastmod tracks the newest public task we've published.
    latest_task_lastmod = await db.fetch_val(
        "SELECT MAX(updated_at) FROM tasks WHERE is_public = true"
    )
    landing_lastmod = (
        latest_task_lastmod.strftime("%Y-%m-%d")
        if latest_task_lastmod
        else datetime.now().strftime("%Y-%m-%d")
    )

    # Changelog lastmod from the most recent entry in changelog.json.
    changelog_lastmod = datetime.now().strftime("%Y-%m-%d")
    try:
        changelog_path = Path(settings.changelog_json_path)
        if not changelog_path.is_absolute():
            changelog_path = PROJECT_ROOT / changelog_path
        if changelog_path.exists():
            with open(changelog_path, encoding="utf-8") as f:
                changelog_entries = json.load(f)
                if changelog_entries:
                    # Entries are sorted newest first.
                    changelog_lastmod = changelog_entries[0]["date"]
    except Exception:
        # Fall back to current date if changelog read fails
        pass

    pages: list[dict[str, str]] = [
        {
            "loc": f"{base_url}/",
            "priority": "1.0",
            "changefreq": "daily",
            "lastmod": landing_lastmod,
        },
        {
            "loc": f"{base_url}/changelog",
            "priority": "0.7",
            "changefreq": "weekly",
            "lastmod": changelog_lastmod,
        },
        # /explore aggregates recent triggered watches; the SSG page revalidates
        # every 5 minutes, so daily change cadence is the right Google hint.
        {
            "loc": f"{base_url}/explore",
            "priority": "0.8",
            "changefreq": "daily",
            "lastmod": landing_lastmod,
        },
    ]

    # Public tasks. Cap at 5000 to keep the sitemap under the 50k / 50 MiB
    # sitemap-protocol limit and the response under a sane time budget; if
    # the public task count grows past that, split into paged sitemaps via
    # the sitemap-index. Sorted by updated_at DESC so the freshest URLs hit
    # crawlers first when budgets are tight.
    public_tasks = await db.fetch_all(
        """
        SELECT id, updated_at
        FROM tasks
        WHERE is_public = true
        ORDER BY updated_at DESC NULLS LAST
        LIMIT 5000
        """
    )
    for row in public_tasks:
        task_id = row["id"]
        updated = row["updated_at"]
        lastmod = (
            updated.strftime("%Y-%m-%d")
            if updated
            else datetime.now().strftime("%Y-%m-%d")
        )
        pages.append(
            {
                "loc": f"{base_url}/tasks/{task_id}",
                "priority": "0.6",
                "changefreq": "weekly",
                "lastmod": lastmod,
            }
        )

    for page in pages:
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = page["loc"]
        ET.SubElement(url_elem, "changefreq").text = page["changefreq"]
        ET.SubElement(url_elem, "priority").text = page["priority"]
        ET.SubElement(url_elem, "lastmod").text = page["lastmod"]

    xml_output = ET.tostring(urlset, encoding="utf-8", xml_declaration=True)

    return Response(content=xml_output, media_type="application/xml")


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
    # added — auth-gated SPA routes that should not be indexed. /tasks/
    # stays Allow (covers public task pages in sitemap-dynamic).
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
