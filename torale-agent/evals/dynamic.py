"""Dynamic case generators that fetch real-world data for evaluation."""

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pydantic_evals import Case, Dataset

from evals.evaluators import (
    CUSTOM_EVALUATORS,
    FetchUrlUsed,
    ReasonableNextRun,
    SearchToolUsed,
    SourcesWhenNotifying,
)
from evals.models import MonitoringCase, MonitoringCaseInput, MonitoringCaseMetadata
from models import MonitoringResponse

logger = logging.getLogger(__name__)


def _meta(category: str) -> MonitoringCaseMetadata:
    return MonitoringCaseMetadata(
        category=category,
        source="dynamic",
        generated_at=datetime.now(UTC).isoformat(),
    )


async def generate_weather_cases(client: httpx.AsyncClient) -> list[MonitoringCase]:
    """Generate weather monitoring cases using Open-Meteo API."""
    cases: list[MonitoringCase] = []
    cities = [
        ("London", 51.5, -0.12),
        ("New York", 40.71, -74.01),
        ("Tokyo", 35.68, 139.69),
    ]

    for city, lat, lon in cities:
        resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,weather_code",
                "forecast_days": 1,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        weather_code = data["current"]["weather_code"]

        # Severe weather codes: thunderstorm (95-99), heavy rain (65-67), snow (75-77)
        if weather_code >= 65:
            cases.append(
                Case(
                    name=f"Weather Alert {city} (active)",
                    inputs=MonitoringCaseInput(
                        search_query=f"Is there a severe weather warning for {city} right now?",
                        condition_description=f"Severe weather conditions detected in {city}",
                        category="Weather",
                        notify_behavior="always",
                    ),
                    metadata=_meta("Weather"),
                )
            )
        else:
            # Should NOT trigger notification — tests false-positive resistance
            cases.append(
                Case(
                    name=f"Weather Alert {city} (clear)",
                    inputs=MonitoringCaseInput(
                        search_query=f"Is there a severe weather warning for {city} right now?",
                        condition_description=f"Active severe weather warning (tornado, hurricane, or blizzard) issued by official meteorological agency for {city}",
                        category="Weather",
                        notify_behavior="always",
                    ),
                    metadata=_meta("Weather"),
                )
            )

    return cases


async def generate_stock_cases(client: httpx.AsyncClient) -> list[MonitoringCase]:
    """Generate stock monitoring cases using Yahoo Finance RSS."""
    cases: list[MonitoringCase] = []

    tickers = [
        ("AAPL", "Apple"),
        ("GOOGL", "Alphabet"),
        ("MSFT", "Microsoft"),
    ]

    for ticker, company in tickers:
        resp = await client.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
            params={"interval": "1d", "range": "1d"},
            headers={"User-Agent": "torale-eval/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]

        # Case 1: threshold above current price (should NOT notify)
        cases.append(
            Case(
                name=f"{ticker} Above {price + 10:.0f} (false)",
                inputs=MonitoringCaseInput(
                    search_query=f"What is the current stock price of {company} ({ticker})?",
                    condition_description=f"{ticker} stock price rises above ${price + 10:.2f}",
                    category="Finance",
                    notify_behavior="once",
                ),
                metadata=_meta("Finance"),
            )
        )

        # Case 2: threshold below current price (should notify)
        cases.append(
            Case(
                name=f"{ticker} Below {price - 10:.0f} (true)",
                inputs=MonitoringCaseInput(
                    search_query=f"What is the current stock price of {company} ({ticker})?",
                    condition_description=f"{ticker} stock price drops below ${price - 10:.2f}",
                    category="Finance",
                    notify_behavior="once",
                ),
                metadata=_meta("Finance"),
            )
        )

    return cases


async def _generate_rss_cases(
    client: httpx.AsyncClient,
    url: str,
    category: str,
    name_prefix: str,
    query_template: str,
    condition_template: str,
) -> list[MonitoringCase]:
    """Generate monitoring cases from a BBC RSS feed."""
    cases: list[MonitoringCase] = []

    resp = await client.get(url)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    items = root.findall(".//item")[:3]

    for item in items:
        title = item.findtext("title", "")
        if not title:
            continue

        cases.append(
            Case(
                name=f"{name_prefix}: {title[:50]}",
                inputs=MonitoringCaseInput(
                    search_query=query_template.format(title=title),
                    condition_description=condition_template.format(title=title),
                    category=category,
                    notify_behavior="always",
                ),
                metadata=_meta(category),
            )
        )

    return cases


async def generate_news_cases(client: httpx.AsyncClient) -> list[MonitoringCase]:
    """Generate monitoring cases from current BBC News headlines via RSS."""
    return await _generate_rss_cases(
        client,
        url="https://feeds.bbci.co.uk/news/rss.xml",
        category="News",
        name_prefix="News",
        query_template="What are the latest developments on: {title}?",
        condition_template="New significant developments reported about: {title}",
    )


async def generate_sports_cases(client: httpx.AsyncClient) -> list[MonitoringCase]:
    """Generate sports monitoring cases from BBC Sport RSS."""
    return await _generate_rss_cases(
        client,
        url="https://feeds.bbci.co.uk/sport/rss.xml",
        category="Sports",
        name_prefix="Sport",
        query_template="What is the latest on: {title}?",
        condition_template="New confirmed development regarding: {title}",
    )


async def generate_webpage_cases(client: httpx.AsyncClient) -> list[MonitoringCase]:
    """Generate cases that require fetch_url to verify page content.

    These cases point at specific URLs where search engines won't have
    the live page content — forcing the agent to fetch directly.
    """
    pages = [
        {
            "name": "GitHub Trending Python",
            "query": "Check https://github.com/trending/python?since=daily for today's trending Python repos",
            "condition": "A repository related to AI/ML/LLMs is currently trending on GitHub's Python page. Verify by fetching the page directly — search results won't have today's trending list",
            "category": "Tech",
        },
        {
            "name": "Hacker News Front Page",
            "query": "Check https://news.ycombinator.com/ for current front page stories",
            "condition": "A story about LLMs or AI agents is on the Hacker News front page right now. You must fetch the page directly to see the current front page — search results show old snapshots",
            "category": "Tech",
        },
        {
            "name": "Python PyPI New Releases",
            "query": "Check https://pypi.org/search/?q=&o=-created for the newest packages published to PyPI",
            "condition": "A new AI/ML-related package was published to PyPI today. Fetch the page directly to see real-time listings",
            "category": "Tech",
        },
    ]

    return [
        Case(
            name=f"Webpage: {page['name']}",
            inputs=MonitoringCaseInput(
                search_query=page["query"],
                condition_description=page["condition"],
                category=page["category"],
                notify_behavior="always",
            ),
            metadata=_meta(page["category"]),
        )
        for page in pages
    ]


async def generate_all() -> list[MonitoringCase]:
    """Run all generators concurrently, catching individual failures."""
    generators = [
        ("weather", generate_weather_cases),
        ("stocks", generate_stock_cases),
        ("news", generate_news_cases),
        ("sports", generate_sports_cases),
        ("webpage", generate_webpage_cases),
    ]

    all_cases: list[MonitoringCase] = []

    async with httpx.AsyncClient(timeout=10) as client:
        tasks = {name: asyncio.create_task(gen(client)) for name, gen in generators}

        for name, task in tasks.items():
            try:
                cases = await task
                all_cases.extend(cases)
                logger.info("Generated %d %s cases", len(cases), name)
            except Exception:
                logger.exception("Failed to generate %s cases", name)

    return all_cases


async def generate_and_save(output_dir: Path) -> Path:
    """Generate dynamic cases and save to a timestamped YAML file."""
    cases = await generate_all()

    if not cases:
        raise RuntimeError("No dynamic cases generated — all generators failed")

    dataset = Dataset[MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata](
        cases=cases,
        evaluators=[
            SourcesWhenNotifying(),
            ReasonableNextRun(),
            SearchToolUsed(),
            FetchUrlUsed(),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"{timestamp}.yaml"
    dataset.to_file(path, schema_path=None, custom_evaluator_types=CUSTOM_EVALUATORS)

    return path
