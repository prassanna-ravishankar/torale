"""Sitemap generation for SEO."""

from datetime import datetime

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
    tasks_query = """
        SELECT t.slug, u.username, t.updated_at
        FROM tasks t
        INNER JOIN users u ON t.user_id = u.id
        WHERE t.is_public = true
        ORDER BY t.updated_at DESC
    """

    tasks = await db.fetch_all(tasks_query)

    # Build XML sitemap
    base_url = settings.frontend_url or "https://torale.ai"

    # Start XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Static pages
    static_pages = [
        {"loc": f"{base_url}/", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{base_url}/explore", "priority": "0.9", "changefreq": "hourly"},
    ]

    for page in static_pages:
        xml += "  <url>\n"
        xml += f"    <loc>{page['loc']}</loc>\n"
        xml += f"    <changefreq>{page['changefreq']}</changefreq>\n"
        xml += f"    <priority>{page['priority']}</priority>\n"
        xml += "  </url>\n"

    # Public task pages
    for task in tasks:
        task_url = f"{base_url}/tasks/@{task['username']}/{task['slug']}"
        lastmod = task["updated_at"].strftime("%Y-%m-%d")

        xml += "  <url>\n"
        xml += f"    <loc>{task_url}</loc>\n"
        xml += f"    <lastmod>{lastmod}</lastmod>\n"
        xml += "    <changefreq>weekly</changefreq>\n"
        xml += "    <priority>0.8</priority>\n"
        xml += "  </url>\n"

    xml += "</urlset>"

    return Response(content=xml, media_type="application/xml")


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
Allow: /tasks/@

Disallow: /api/
Disallow: /auth/
Disallow: /signin
Disallow: /signup
Disallow: /settings

Sitemap: {base_url}/sitemap.xml
"""

    return Response(content=robots, media_type="text/plain")
