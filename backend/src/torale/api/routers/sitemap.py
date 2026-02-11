"""Sitemap generation for SEO."""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Response

from torale.core.config import settings
from torale.core.database import Database, get_db

router = APIRouter(tags=["seo"])


@router.get("/sitemap.xml")
async def generate_sitemap(db: Database = Depends(get_db)):
    """
    Generate dynamic sitemap.xml for search engines.

    Includes:
    - Static pages (landing, explore)
    - Public task pages (vanity URLs)
    """
    # Get all public tasks with username and updated_at
    # TODO: At scale (>10k public tasks), implement sitemap index pattern:
    # - Split into multiple sitemap files (50k URLs each per Google guidelines)
    # - Use sitemap index file to reference individual sitemaps
    # - Consider caching the generated sitemap with periodic regeneration
    tasks_query = """
        SELECT t.slug, u.username, t.updated_at
        FROM tasks t
        INNER JOIN users u ON t.user_id = u.id
        WHERE t.is_public = true
        ORDER BY t.updated_at DESC
    """

    tasks = await db.fetch_all(tasks_query)

    # Build XML sitemap using xml.etree
    base_url = settings.frontend_url or "https://torale.ai"

    # Create root element with namespace
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Get max updated_at from public tasks for explore page lastmod
    explore_lastmod = (
        max(task["updated_at"] for task in tasks).strftime("%Y-%m-%d")
        if tasks
        else datetime.now().strftime("%Y-%m-%d")
    )

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
        task_url = f"{base_url}/t/{task['username']}/{task['slug']}"
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
    # Find project root by looking for pyproject.toml marker file
    project_root = Path(__file__).resolve()
    while not (project_root / "pyproject.toml").exists():
        if project_root.parent == project_root:
            raise FileNotFoundError("Could not find project root containing 'pyproject.toml'")
        project_root = project_root.parent
    changelog_path = project_root / "frontend" / "public" / "changelog.json"

    # Read and parse changelog
    with open(changelog_path, encoding="utf-8") as f:
        entries = json.load(f)

    # Take first MAX_RSS_ENTRIES entries
    MAX_RSS_ENTRIES = 50
    entries = entries[:MAX_RSS_ENTRIES]

    base_url = settings.frontend_url or "https://torale.ai"

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
    Generate robots.txt for search engine crawlers.

    Allows:
    - All public pages
    - Sitemap location

    Disallows:
    - Auth pages
    - API endpoints
    - Admin endpoints
    """
    base_url = settings.frontend_url or "https://torale.ai"

    robots = f"""User-agent: *
Allow: /
Allow: /explore
Allow: /t/

Disallow: /api/
Disallow: /auth/
Disallow: /signin
Disallow: /signup
Disallow: /settings
Disallow: /admin/

Sitemap: {base_url}/sitemap.xml
"""

    return Response(content=robots, media_type="text/plain")
