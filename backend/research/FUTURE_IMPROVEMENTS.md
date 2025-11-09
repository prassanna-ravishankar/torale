# Future Improvements for Research Harness

## Dynamic Ground Truth Expansion

Currently, the harness uses dynamic GT only for weather queries. This document outlines potential expansions for live event verification.

### Current State
- ✅ **Weather**: Open-Meteo API for real-time forecast validation
- ❌ **Product Releases**: Static GT (verified as of Nov 8, 2025)
- ❌ **Availability**: Static GT (may become stale)
- ❌ **Boolean Facts**: Static GT (historical events)

### Proposed Expansions

#### Tier 1: High Value (Good APIs Available)

**Stock & Availability Checks**
- Use Case: "Is PlayStation 5 in stock at Best Buy?"
- APIs:
  - Best Buy Product API (requires free API key)
  - Amazon Product Advertising API (requires account)
  - CamelCamelCamel / Keepa for price tracking
- Implementation: Add `_check_stock_availability(retailer, product_id)` handler
- Benefit: Always-current test cases for availability queries

**Product Pricing**
- Use Case: "Can I buy RTX 4090 at MSRP?"
- APIs: Same as availability (price comparison APIs)
- Implementation: `_check_price_vs_msrp(product_id, msrp_threshold)`

#### Tier 2: Medium Value (Requires Web Scraping/Unreliable)

**Product Release Dates**
- Use Case: "When is iPhone 17 being released?"
- Options:
  - **Wikidata SPARQL**: Query structured data for release dates
    - Pro: Structured, queryable
    - Con: Can lag behind announcements by days/weeks
  - **Wikipedia API**: Parse product pages
    - Pro: Comprehensive coverage
    - Con: Can be vandalized, requires parsing
  - **RSS Feeds**: Apple Newsroom, Samsung, etc.
    - Pro: Official sources
    - Con: Requires parsing, different formats per vendor
- Implementation: `_check_product_announced(product_name, wikidata_id)`
- Trade-off: May not be real-time enough for "just announced" events

**Event Announcements**
- Use Case: "When is the next Apple event scheduled?"
- Options:
  - Scrape Apple Events page
  - Apple Calendar RSS feed
- Implementation: `_check_apple_event_announced()`

#### Tier 3: Not Recommended

**Historical Boolean Facts**
- Examples: "Has Twitter been rebranded to X?", "Did Trump win 2024 election?"
- Why skip: These are one-time historical events that won't change
- Recommendation: Keep as static GT, update manually when events occur

**Overly-Specific Local Queries**
- Example: "When do swimming pool memberships open for summer 2025?"
- Why skip: Too location-specific, no good APIs
- Recommendation: Remove from test cases or make generic

### Implementation Pattern

```python
# In dynamic_gt.py

def _check_bestbuy_stock(sku: str) -> bool:
    """Check if product is in stock at Best Buy."""
    import requests
    api_key = os.getenv("BESTBUY_API_KEY")
    url = f"https://api.bestbuy.com/v1/products/{sku}.json"
    response = requests.get(url, params={"apiKey": api_key})
    data = response.json()
    return data.get("onlineAvailability", False)

# Add to DYNAMIC_GT_HANDLERS
DYNAMIC_GT_HANDLERS = {
    # ... existing weather handlers ...
    ("ps5", "stock", "best buy"): lambda: _check_bestbuy_stock("6426149"),
    ("rtx 4090", "msrp"): lambda: _check_price_vs_msrp("nvidia-4090", 1599.00),
}
```

### API Requirements

| API | Free Tier | Key Required | Rate Limits | Reliability |
|-----|-----------|--------------|-------------|-------------|
| Open-Meteo | ✅ Yes | ❌ No | Unlimited | ⭐⭐⭐⭐⭐ |
| Best Buy | ✅ Yes | ✅ Yes | 5 req/sec | ⭐⭐⭐⭐ |
| Amazon Product | ❌ Paid | ✅ Yes | 1 req/sec | ⭐⭐⭐⭐ |
| Wikidata SPARQL | ✅ Yes | ❌ No | 60 req/min | ⭐⭐⭐ |
| CamelCamelCamel | 🟡 Limited | ✅ Yes | Varies | ⭐⭐⭐ |

### Recommendation

**Start Simple:**
1. ✅ Keep weather (already done)
2. ➕ Add stock availability for 1-2 products (Best Buy API)
3. ➕ Add price tracking for 1-2 products
4. ⏸️ Keep everything else as static GT with documented verification date

**Rationale:**
- Dynamic GT is most valuable for **time-sensitive data** (weather, stock, prices)
- Less valuable for **one-time events** (product announcements) that can use static GT
- Avoid complexity of maintaining many external APIs
- Focus on **simple, reliable, free APIs** first

### Future Considerations

If the harness becomes a production test suite:
- Add retry logic for API failures
- Implement caching to avoid rate limits
- Add fallback to static GT when API unavailable
- Monitor API health and switch to alternatives if needed
- Consider cost implications of paid APIs at scale

### Discussion Points

Before implementing, consider:
1. **Value vs Effort**: Does dynamic GT for product releases justify Wikidata integration?
2. **Test Stability**: Dynamic tests may fail due to API issues, not approach quality
3. **Cost**: Some APIs (Amazon) require payment - acceptable for research?
4. **Maintenance**: More APIs = more potential breakage points
5. **Test Purpose**: Are we testing search quality or API reliability?

### Related Files

- `research/dynamic_gt.py` - Current implementation
- `research/approaches/weather_gt.py` - Weather API integration example
- `research/test_cases.py` - Test cases that could benefit from dynamic GT
