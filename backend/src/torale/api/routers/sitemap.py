"""Sitemap generation for SEO."""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Response

from torale.core.config import PROJECT_ROOT, settings
from torale.core.database import Database, get_db

# Register atom namespace once at module level (avoids per-request global mutation)
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")

router = APIRouter(tags=["seo"])


@router.get("/sitemap.xml")
async def generate_sitemap_index(db: Database = Depends(get_db)):
    """
    Sitemap index pointing at the static (frontend-served) and dynamic (backend)
    child sitemaps. Frontend owns enumerated SEO routes (publicRoutes.ts);
    backend owns DB-derived public task pages.
    """
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
async def generate_sitemap_dynamic(db: Database = Depends(get_db)):
    """
    Dynamic sitemap covering DB-derived public pages: landing, explore, changelog,
    and every public task. Linked from /sitemap.xml (the index).
    """
    tasks_query = """
        SELECT t.id, t.updated_at
        FROM tasks t
        WHERE t.is_public = true
        ORDER BY t.updated_at DESC
    """

    tasks = await db.fetch_all(tasks_query)

    # Build XML sitemap using xml.etree
    base_url = settings.frontend_url

    # Create root element with namespace
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Get max updated_at from public tasks for explore page lastmod
    explore_lastmod = (
        max(task["updated_at"] for task in tasks).strftime("%Y-%m-%d")
        if tasks
        else datetime.now().strftime("%Y-%m-%d")
    )

    # Get changelog lastmod from most recent entry
    changelog_lastmod = datetime.now().strftime("%Y-%m-%d")
    try:
        changelog_path = Path(settings.changelog_json_path)
        if not changelog_path.is_absolute():
            changelog_path = PROJECT_ROOT / changelog_path
        if changelog_path.exists():
            with open(changelog_path, encoding="utf-8") as f:
                changelog_entries = json.load(f)
                if changelog_entries:
                    # Get date from most recent entry (entries are sorted newest first)
                    changelog_lastmod = changelog_entries[0]["date"]
    except Exception:
        # Fall back to current date if changelog read fails
        pass

    # Static pages with lastmod
    static_pages = [
        {
            "loc": f"{base_url}/",
            "priority": "1.0",
            "changefreq": "daily",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "loc": f"{base_url}/explore",
            "priority": "0.9",
            "changefreq": "hourly",
            "lastmod": explore_lastmod,
        },
        {
            "loc": f"{base_url}/changelog",
            "priority": "0.7",
            "changefreq": "weekly",
            "lastmod": changelog_lastmod,
        },
    ]

    for page in static_pages:
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = page["loc"]
        ET.SubElement(url_elem, "changefreq").text = page["changefreq"]
        ET.SubElement(url_elem, "priority").text = page["priority"]
        if "lastmod" in page:
            ET.SubElement(url_elem, "lastmod").text = page["lastmod"]

    # Public task pages
    for task in tasks:
        task_url = f"{base_url}/tasks/{task['id']}"
        lastmod = task["updated_at"].strftime("%Y-%m-%d")

        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = task_url
        ET.SubElement(url_elem, "lastmod").text = lastmod
        ET.SubElement(url_elem, "changefreq").text = "weekly"
        ET.SubElement(url_elem, "priority").text = "0.8"

    # Convert to XML with declaration
    xml_output = ET.tostring(urlset, encoding="utf-8", xml_declaration=True)

    return Response(content=xml_output, media_type="application/xml")


@router.get("/changelog.xml")
async def generate_changelog_rss():
    """
    Generate RSS 2.0 feed for changelog.

    Reads changelog.json from frontend/public and converts to RSS format.
    Includes first 50 entries with proper RFC-2822 date formatting.
    """
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
    ET.SubElement(channel, "title").text = "Torale Changelog"
    ET.SubElement(channel, "link").text = f"{base_url}/changelog"
    ET.SubElement(channel, "description").text = (
        "Latest updates, features, and improvements to Torale - "
        "the AI-powered grounded search monitoring platform"
    )
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


@router.get("/robots.txt")
async def robots_txt():
    """
    robots.txt for search engine crawlers. Non-prod hosts return a blanket
    disallow so staging/preview deployments don't get indexed.
    """
    base_url = settings.frontend_url

    if base_url != "https://torale.ai":
        return Response(content="User-agent: *\nDisallow: /\n", media_type="text/plain")

    robots = f"""User-agent: *
Allow: /
Allow: /explore
Allow: /tasks/

Disallow: /api/
Disallow: /auth/
Disallow: /signin
Disallow: /signup
Disallow: /settings
Disallow: /admin/

Sitemap: {base_url}/sitemap.xml
"""

    return Response(content=robots, media_type="text/plain")
