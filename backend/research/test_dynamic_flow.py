"""
Demonstration of how dynamic ground truth translates to True/False.

Shows the complete flow from API → boolean GT → accuracy evaluation.
"""

from approaches.weather_gt import CITIES, get_tomorrow_rain
from dynamic_gt import get_dynamic_ground_truth
from test_cases import TEST_EXPERIMENTS

print("=" * 80)
print("DYNAMIC GROUND TRUTH FLOW: API → Boolean")
print("=" * 80)

# Step 1: Raw API call
print("\n📡 STEP 1: Raw API Call")
print("-" * 80)
result = get_tomorrow_rain(*CITIES["seattle"])
print("Open-Meteo API Response for Seattle:")
print(f"  precipitation_mm: {result['precipitation_mm']}")
print(f"  rain_mm: {result['rain_mm']}")
print(f"  date: {result['date']}")
print(f"  timezone: {result['timezone']}")

# Step 2: Translation to boolean
print("\n🔄 STEP 2: Translation to Boolean")
print("-" * 80)
print("Logic: will_rain = (precipitation_mm > 0)")
print(f"  {result['precipitation_mm']} > 0 = {result['will_rain']}")
print(f"\n✅ Ground Truth (boolean): {result['will_rain']}")

# Step 3: Get experiment with dynamic GT
print("\n📝 STEP 3: Experiment with Dynamic GT")
print("-" * 80)
weather_exp = next(e for e in TEST_EXPERIMENTS if e.category == "weather")
print(f"Query: {weather_exp.search_query}")
print(f"Condition: {weather_exp.condition_description}")
print(f"expected_outcome in code: {weather_exp.expected_outcome}")

# Step 4: Dynamic GT resolution
print("\n⚙️  STEP 4: Dynamic GT Resolution (at runtime)")
print("-" * 80)
resolved_gt = get_dynamic_ground_truth(weather_exp)
print(f"get_dynamic_ground_truth() returns: {resolved_gt}")
print("  (This is what replaces 'None' during test execution)")

# Step 5: How it's used in harness
print("\n🎯 STEP 5: Usage in Harness")
print("-" * 80)
print("""
# In harness.py:
expected = experiment.expected_outcome  # None for weather
if expected is None:
    expected = get_dynamic_ground_truth(experiment)  # Returns: False

# Now expected = False (for Seattle, Nov 9, 2025)

# Then accuracy is calculated:
accuracy = evaluate_result["condition_met"] == expected
# If LLM says "no rain" → condition_met=False
# accuracy = False == False → True ✅
""")

# Step 6: Full example
print("\n📊 STEP 6: Full Example Scenario")
print("-" * 80)

scenarios = [
    {
        "llm_prediction": False,
        "reasoning": "LLM correctly predicts no rain",
    },
    {
        "llm_prediction": True,
        "reasoning": "LLM incorrectly predicts rain",
    },
]

for i, scenario in enumerate(scenarios, 1):
    print(f"\nScenario {i}: {scenario['reasoning']}")
    print(f"  Ground Truth (from API): {resolved_gt}")
    print(f"  LLM condition_met: {scenario['llm_prediction']}")
    accuracy = scenario["llm_prediction"] == resolved_gt
    print(
        f"  Accuracy: {scenario['llm_prediction']} == {resolved_gt} = {accuracy} {'✅' if accuracy else '❌'}"
    )

print("\n" + "=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print("""
expected_outcome=None means "check at runtime"

When test runs:
  1. API call: get_tomorrow_rain(seattle) → {"will_rain": False, ...}
  2. Extract boolean: will_rain = False
  3. Compare: LLM's answer == False
  4. Calculate accuracy

This makes the test case ALWAYS current with real weather!
""")
