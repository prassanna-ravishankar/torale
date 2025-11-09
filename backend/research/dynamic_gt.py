"""
Dynamic ground truth evaluator for test cases that need real-time data.

This module provides helpers to evaluate ground truth for test cases that
depend on current state (like weather, prices, availability, etc).
"""

from approaches.weather_gt import CITIES, get_tomorrow_rain


def _check_rain_tomorrow(city_key: str) -> bool:
    """Check if it will rain tomorrow in the specified city."""
    result = get_tomorrow_rain(*CITIES[city_key])
    return result["will_rain"]


# Map query patterns to handler functions
# Each key is a tuple of keywords that must all be present in the query
DYNAMIC_GT_HANDLERS = {
    ("rain", "seattle", "tomorrow"): lambda: _check_rain_tomorrow("seattle"),
    ("rain", "san francisco", "tomorrow"): lambda: _check_rain_tomorrow("san_francisco"),
    ("rain", "new york", "tomorrow"): lambda: _check_rain_tomorrow("new_york"),
    # Add more dynamic checks here as needed
    # e.g., ("bitcoin", "price", "above"): lambda: _check_bitcoin_price_above(threshold),
    # ("ps5", "stock", "best buy"): lambda: _check_bestbuy_stock("ps5"),
}


def get_dynamic_ground_truth(experiment) -> bool:
    """
    Get ground truth for experiments that require real-time data.

    Args:
        experiment: Experiment object with expected_outcome=None for dynamic GT

    Returns:
        bool - The actual expected outcome based on real-time data
    """
    query = experiment.search_query.lower()

    # Try to match query against registered handlers
    for keywords, handler in DYNAMIC_GT_HANDLERS.items():
        if all(keyword in query for keyword in keywords):
            return handler()

    # If no dynamic GT found, raise error
    raise ValueError(f"No dynamic ground truth handler for query: {experiment.search_query}")


if __name__ == "__main__":
    from test_cases import TEST_EXPERIMENTS

    print("Testing dynamic ground truth...\n")

    for exp in TEST_EXPERIMENTS:
        if exp.expected_outcome is None:
            try:
                gt = get_dynamic_ground_truth(exp)
                print(f"Query: {exp.search_query}")
                print(f"Ground truth: {gt}\n")
            except ValueError as e:
                print(f"Error: {e}\n")
