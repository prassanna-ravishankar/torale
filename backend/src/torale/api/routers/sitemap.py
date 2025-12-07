"""Sitemap generation for SEO."""

import xml.etree.ElementTree as ET

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

    # Static pages
    static_pages = [
        {"loc": f"{base_url}/", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{base_url}/explore", "priority": "0.9", "changefreq": "hourly"},
    ]

    for page in static_pages:
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = page["loc"]
        ET.SubElement(url_elem, "changefreq").text = page["changefreq"]
        ET.SubElement(url_elem, "priority").text = page["priority"]

    # Public task pages
    for task in tasks:
        task_url = f"{base_url}/@{task['username']}/{task['slug']}"
        lastmod = task["updated_at"].strftime("%Y-%m-%d")

        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = task_url
        ET.SubElement(url_elem, "lastmod").text = lastmod
        ET.SubElement(url_elem, "changefreq").text = "weekly"
        ET.SubElement(url_elem, "priority").text = "0.8"

    # Convert to XML with declaration
    xml_output = ET.tostring(urlset, encoding="utf-8", xml_declaration=True)

    return Response(content=xml_output, media_type="application/xml")


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
    """
    base_url = settings.frontend_url or "https://torale.ai"

    robots = f"""User-agent: *
Allow: /
Allow: /explore
Allow: /@

Disallow: /api/
Disallow: /auth/
Disallow: /signin
Disallow: /signup
Disallow: /settings

Sitemap: {base_url}/sitemap.xml
"""

    return Response(content=robots, media_type="text/plain")
