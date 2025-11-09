"""
Dynamic ground truth evaluator for test cases that need real-time data.

This module provides helpers to evaluate ground truth for test cases that
depend on current state (like weather, prices, availability, etc).
"""

from approaches.weather_gt import CITIES, get_tomorrow_rain


def get_dynamic_ground_truth(experiment) -> bool:
    """
    Get ground truth for experiments that require real-time data.

    Args:
        experiment: Experiment object with expected_outcome=None for dynamic GT

    Returns:
        bool - The actual expected outcome based on real-time data
    """
    query = experiment.search_query.lower()

    # Weather checks
    if "rain" in query and "seattle" in query and "tomorrow" in query:
        result = get_tomorrow_rain(*CITIES["seattle"])
        return result["will_rain"]

    if "rain" in query and "san francisco" in query and "tomorrow" in query:
        result = get_tomorrow_rain(*CITIES["san_francisco"])
        return result["will_rain"]

    if "rain" in query and "new york" in query and "tomorrow" in query:
        result = get_tomorrow_rain(*CITIES["new_york"])
        return result["will_rain"]

    # Add more dynamic checks here as needed
    # e.g., Bitcoin price, stock availability, etc.

    # If no dynamic GT found, raise error
    raise ValueError(
        f"No dynamic ground truth handler for query: {experiment.search_query}"
    )


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
