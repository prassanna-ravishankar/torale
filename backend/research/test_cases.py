"""
Test cases for grounded search evaluation.

These experiments cover different categories and notify behaviors to test
various aspects of the grounded search monitoring system.
"""

from harness import Experiment

# Test experiments covering diverse scenarios
# Ground truth accurate as of November 8, 2025
TEST_EXPERIMENTS = [
    # Product releases (once behavior - stop after first detection)
    Experiment(
        search_query="When is the next iPhone being released?",
        condition_description="A specific release date or month has been officially announced",
        expected_outcome=True,  # iPhone 17 announced Sept 9, 2025, released Sept 19, 2025
        notify_behavior="once",
        category="product_release",
    ),
    Experiment(
        search_query="When will GPT-5 be released?",
        condition_description="OpenAI has announced an official release date for GPT-5",
        expected_outcome=True,  # GPT-5 released August 7, 2025
        notify_behavior="once",
        category="product_release",
    ),
    # Availability checks (always behavior - notify every check)
    Experiment(
        search_query="Is PlayStation 5 in stock at Best Buy?",
        condition_description="PS5 is currently available for purchase at Best Buy",
        expected_outcome=True,  # Generally available now
        notify_behavior="always",
        category="availability",
    ),
    Experiment(
        search_query="Can I buy Nvidia RTX 4090 at MSRP?",
        condition_description="RTX 4090 is available at manufacturer's suggested retail price",
        expected_outcome=False,  # Typically above MSRP or out of stock
        notify_behavior="always",
        category="availability",
    ),
    # Date announcements (track_state behavior - notify on change)
    Experiment(
        search_query="When do swimming pool memberships open for summer 2025?",
        condition_description="Summer 2025 pool membership registration has opened",
        expected_outcome=False,  # Too early as of Jan 2025
        notify_behavior="track_state",
        category="date_announcement",
    ),
    Experiment(
        search_query="When is the next Apple event scheduled?",
        condition_description="Apple has announced the date for their next event",
        expected_outcome=False,  # Depends on timing
        notify_behavior="track_state",
        category="date_announcement",
    ),
    # Boolean facts (once behavior - simple yes/no)
    Experiment(
        search_query="Has Twitter been rebranded to X?",
        condition_description="Twitter has officially changed its name to X",
        expected_outcome=True,  # Already happened
        notify_behavior="once",
        category="boolean_fact",
    ),
    Experiment(
        search_query="Has SpaceX successfully landed humans on Mars?",
        condition_description="SpaceX has completed a crewed mission to Mars",
        expected_outcome=False,  # Not yet
        notify_behavior="once",
        category="boolean_fact",
    ),
    # Removed: Bitcoin price test - no clear true/false answer for "current price"
    # Price tracking should use specific thresholds with dynamic GT instead
    # Weather with dynamic ground truth (uses Open-Meteo API)
    Experiment(
        search_query="Is it going to rain tomorrow in Seattle?",
        condition_description="Weather forecast shows rain tomorrow in Seattle, WA",
        expected_outcome=None,  # Dynamic: Check weather_gt.get_tomorrow_rain(47.6062, -122.3321)
        notify_behavior="once",
        category="weather",
    ),
    # Additional 2025 events (verified ground truth as of Nov 8, 2025)
    Experiment(
        search_query="Has Nintendo announced the Switch 2?",
        condition_description="Nintendo has officially announced the Nintendo Switch 2 console",
        expected_outcome=True,  # Announced January 16, 2025
        notify_behavior="once",
        category="product_release",
    ),
    Experiment(
        search_query="Did Donald Trump win the 2024 US presidential election?",
        condition_description="Donald Trump won the 2024 presidential election",
        expected_outcome=True,  # Won with 312 electoral votes, inaugurated Jan 20, 2025
        notify_behavior="once",
        category="boolean_fact",
    ),
    Experiment(
        search_query="Has Apple released Vision Pro with M5 chip?",
        condition_description="Apple has released an updated Vision Pro with M5 chip",
        expected_outcome=True,  # Released October 22, 2025
        notify_behavior="once",
        category="product_release",
    ),
    Experiment(
        search_query="Is Samsung Galaxy S25 available for purchase?",
        condition_description="Samsung Galaxy S25 is available to buy",
        expected_outcome=True,  # Released January/February 2025
        notify_behavior="always",
        category="availability",
    ),
    Experiment(
        search_query="Has SpaceX Starship reached orbit?",
        condition_description="SpaceX Starship has successfully completed an orbital flight (not suborbital)",
        expected_outcome=False,  # 11 suborbital tests as of Oct 2025, no orbital yet
        notify_behavior="once",
        category="boolean_fact",
    ),
    Experiment(
        search_query="Did the WHO declare COVID-19 pandemic officially over?",
        condition_description="WHO has declared the COVID-19 pandemic is officially over",
        expected_outcome=False,  # Ended PHEIC in May 2023, but not declared "over"
        notify_behavior="once",
        category="boolean_fact",
    ),
    Experiment(
        search_query="Has Meta released Quest 4 VR headset?",
        condition_description="Meta Quest 4 has been released and is available",
        expected_outcome=False,  # Delayed to 2027, not released as of Nov 2025
        notify_behavior="once",
        category="product_release",
    ),
    Experiment(
        search_query="Is Windows 12 available to download?",
        condition_description="Microsoft Windows 12 has been officially released",
        expected_outcome=False,  # Not announced or released, focus on Windows 11 updates
        notify_behavior="once",
        category="product_release",
    ),
]

# Filtered subsets for focused testing
PRODUCT_RELEASE_EXPERIMENTS = [e for e in TEST_EXPERIMENTS if e.category == "product_release"]
AVAILABILITY_EXPERIMENTS = [e for e in TEST_EXPERIMENTS if e.category == "availability"]
BOOLEAN_FACT_EXPERIMENTS = [e for e in TEST_EXPERIMENTS if e.category == "boolean_fact"]

# Experiments grouped by notify behavior
ONCE_EXPERIMENTS = [e for e in TEST_EXPERIMENTS if e.notify_behavior == "once"]
ALWAYS_EXPERIMENTS = [e for e in TEST_EXPERIMENTS if e.notify_behavior == "always"]
TRACK_STATE_EXPERIMENTS = [e for e in TEST_EXPERIMENTS if e.notify_behavior == "track_state"]
