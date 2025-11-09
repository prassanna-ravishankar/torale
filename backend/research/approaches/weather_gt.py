"""
Dynamic ground truth for weather queries using Open-Meteo API.

This provides real-time weather data to validate grounded search results.
No API key required - free for non-commercial use up to 10,000 calls/day.

API Docs: https://open-meteo.com/en/docs
"""

from datetime import datetime, timedelta

import requests


def get_tomorrow_rain(latitude: float = 37.7749, longitude: float = -122.4194) -> dict:
    """
    Check if it will rain tomorrow at a specific location.

    Args:
        latitude: Latitude coordinate (default: San Francisco)
        longitude: Longitude coordinate (default: San Francisco)

    Returns:
        dict with keys:
            - will_rain: bool - True if rain expected tomorrow
            - precipitation_mm: float - Total precipitation in mm
            - rain_mm: float - Total rain in mm
            - location: str - Location name
            - date: str - Tomorrow's date
    """
    # Get tomorrow's date
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    # Query Open-Meteo API
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "precipitation_sum,rain_sum",
        "forecast_days": 2,
        "timezone": "auto",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Extract tomorrow's data (index 1, since index 0 is today)
    tomorrow_precip = data["daily"]["precipitation_sum"][1]
    tomorrow_rain = data["daily"]["rain_sum"][1]

    # Determine if it will rain (>0mm of precipitation)
    will_rain = tomorrow_precip > 0

    return {
        "will_rain": will_rain,
        "precipitation_mm": tomorrow_precip,
        "rain_mm": tomorrow_rain,
        "location": f"lat={latitude}, lon={longitude}",
        "date": tomorrow_str,
        "timezone": data.get("timezone", "UTC"),
    }


def get_weather_condition(
    latitude: float,
    longitude: float,
    days_ahead: int = 1,
    condition_check: str = "rain",
) -> dict:
    """
    Generic weather condition checker for any location and timeframe.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        days_ahead: Number of days in future (1 = tomorrow, 2 = day after, etc)
        condition_check: Type of check ('rain', 'snow', 'temperature_above_20c', etc)

    Returns:
        dict with condition_met and relevant data
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "precipitation_sum,rain_sum,snowfall_sum,temperature_2m_max,temperature_2m_min",
        "forecast_days": days_ahead + 1,
        "timezone": "auto",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Get the target day's data
    idx = days_ahead
    precip = data["daily"]["precipitation_sum"][idx]
    rain = data["daily"]["rain_sum"][idx]
    snow = data["daily"]["snowfall_sum"][idx]
    temp_max = data["daily"]["temperature_2m_max"][idx]
    temp_min = data["daily"]["temperature_2m_min"][idx]

    # Evaluate condition
    condition_met = False
    reasoning = ""

    if condition_check == "rain":
        condition_met = rain > 0
        reasoning = f"Rain: {rain}mm" if condition_met else f"No rain (precipitation: {precip}mm)"
    elif condition_check == "snow":
        condition_met = snow > 0
        reasoning = f"Snow: {snow}mm" if condition_met else "No snow"
    elif condition_check.startswith("temperature_above_"):
        threshold = float(condition_check.split("_")[-1].replace("c", ""))
        condition_met = temp_max > threshold
        reasoning = f"Max temp: {temp_max}°C (threshold: {threshold}°C)"
    elif condition_check.startswith("temperature_below_"):
        threshold = float(condition_check.split("_")[-1].replace("c", ""))
        condition_met = temp_min < threshold
        reasoning = f"Min temp: {temp_min}°C (threshold: {threshold}°C)"

    target_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    return {
        "condition_met": condition_met,
        "reasoning": reasoning,
        "date": target_date,
        "location": f"lat={latitude}, lon={longitude}",
        "weather_data": {
            "precipitation_mm": precip,
            "rain_mm": rain,
            "snow_mm": snow,
            "temp_max_c": temp_max,
            "temp_min_c": temp_min,
        },
    }


# Common city coordinates for easy testing
CITIES = {
    "san_francisco": (37.7749, -122.4194),
    "new_york": (40.7128, -74.0060),
    "london": (51.5074, -0.1278),
    "tokyo": (35.6762, 139.6503),
    "sydney": (-33.8688, 151.2093),
    "paris": (48.8566, 2.3522),
    "seattle": (47.6062, -122.3321),
}


if __name__ == "__main__":
    # Test the API
    print("Testing Open-Meteo weather ground truth...\n")

    # Test San Francisco
    print("San Francisco:")
    result = get_tomorrow_rain(*CITIES["san_francisco"])
    print(f"  Will it rain tomorrow? {result['will_rain']}")
    print(f"  Precipitation: {result['precipitation_mm']}mm")
    print(f"  Date: {result['date']}\n")

    # Test Seattle (often rainy)
    print("Seattle:")
    result = get_tomorrow_rain(*CITIES["seattle"])
    print(f"  Will it rain tomorrow? {result['will_rain']}")
    print(f"  Precipitation: {result['precipitation_mm']}mm")
    print(f"  Date: {result['date']}\n")

    # Test generic condition checker
    print("New York - Temperature check:")
    result = get_weather_condition(
        *CITIES["new_york"], days_ahead=1, condition_check="temperature_above_10c"
    )
    print(f"  Above 10°C? {result['condition_met']}")
    print(f"  {result['reasoning']}")
