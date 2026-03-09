"""Dynamic case generators that fetch real-world data for evaluation."""

import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pydantic_evals import Case, Dataset

from evals.evaluators import (
    FetchUrlUsed,
    MultiPassProgression,
    ReasonableNextRun,
    SearchToolUsed,
    SourcesWhenNotifying,
)
from evals.models import MonitoringCaseInput, MonitoringCaseMetadata
from models import MonitoringResponse

logger = logging.getLogger(__name__)

CUSTOM_EVALUATORS = [
    SourcesWhenNotifying,
    ReasonableNextRun,
    SearchToolUsed,
    FetchUrlUsed,
    MultiPassProgression,
]

MonitoringCase = Case[
    MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata
]


def _meta(category: str) -> MonitoringCaseMetadata:
    return MonitoringCaseMetadata(
        category=category,
        source="dynamic",
        generated_at=datetime.now(UTC).isoformat(),
    )


async def generate_weather_cases() -> list[MonitoringCase]:
    """Generate weather monitoring cases using Open-Meteo API."""
    cases: list[MonitoringCase] = []
    cities = [
        ("London", 51.5, -0.12),
        ("New York", 40.71, -74.01),
        ("Tokyo", 35.68, 139.69),
    ]

    async with httpx.AsyncClient(timeout=10) as client:
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
            current = data["current"]
            weather_code = current["weather_code"]

            # Severe weather codes: thunderstorm (95-99), heavy rain (65-67), snow (75-77)
            is_severe = weather_code >= 65

            if is_severe:
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


async def generate_stock_cases() -> list[MonitoringCase]:
    """Generate stock monitoring cases using Yahoo Finance RSS."""
    cases: list[MonitoringCase] = []

    tickers = [
        ("AAPL", "Apple"),
        ("GOOGL", "Alphabet"),
        ("MSFT", "Microsoft"),
    ]

    async with httpx.AsyncClient(timeout=10) as client:
        for ticker, company in tickers:
            # Use Yahoo Finance chart API (public, no key needed)
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


async def generate_news_cases() -> list[MonitoringCase]:
    """Generate monitoring cases from current BBC News headlines via RSS."""
    cases: list[MonitoringCase] = []

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://feeds.bbci.co.uk/news/rss.xml")
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        items = root.findall(".//item")[:3]  # top 3 headlines

        for item in items:
            title = item.findtext("title", "")

            if not title:
                continue

            cases.append(
                Case(
                    name=f"News: {title[:50]}",
                    inputs=MonitoringCaseInput(
                        search_query=f"What are the latest developments on: {title}?",
                        condition_description=f"New significant developments reported about: {title}",
                        category="News",
                        notify_behavior="always",
                    ),
                    metadata=_meta("News"),
                )
            )

    return cases


async def generate_sports_cases() -> list[MonitoringCase]:
    """Generate sports monitoring cases from BBC Sport RSS."""
    cases: list[MonitoringCase] = []

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://feeds.bbci.co.uk/sport/rss.xml")
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        items = root.findall(".//item")[:3]

        for item in items:
            title = item.findtext("title", "")
            if not title:
                continue

            cases.append(
                Case(
                    name=f"Sport: {title[:50]}",
                    inputs=MonitoringCaseInput(
                        search_query=f"What is the latest on: {title}?",
                        condition_description=f"New confirmed development regarding: {title}",
                        category="Sports",
                        notify_behavior="always",
                    ),
                    metadata=_meta("Sports"),
                )
            )

    return cases


async def generate_webpage_cases() -> list[MonitoringCase]:
    """Generate cases that require fetch_url to verify page content.

    These cases point at specific URLs where search engines won't have
    the live page content — forcing the agent to fetch directly.
    """
    cases: list[MonitoringCase] = []

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

    for page in pages:
        cases.append(
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
        )

    return cases


async def generate_all() -> list[MonitoringCase]:
    """Run all generators, catching individual failures."""
    all_cases: list[MonitoringCase] = []

    generators = [
        ("weather", generate_weather_cases),
        ("stocks", generate_stock_cases),
        ("news", generate_news_cases),
        ("sports", generate_sports_cases),
        ("webpage", generate_webpage_cases),
    ]

    for name, gen in generators:
        try:
            cases = await gen()
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
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"{timestamp}.yaml"
    dataset.to_file(path, schema_path=None, custom_evaluator_types=CUSTOM_EVALUATORS)

    return path
