# Torale Agentic Evolution Plan

## Why

### The Problem

Torale currently operates as a **notification tool**: monitor something → detect change → send alert. But notifications are ephemeral. The real value lies in the **structured intelligence** we extract from the chaotic web.

> **Core Insight**: You built a "change detection engine for reality" but are boxing it in as a "notification tool." Notifications are ephemeral; **Intelligence is an asset.**

See [Product Vision Discussion](https://github.com/prassanna-ravishankar/torale/issues/121#issuecomment-3650006660) for the full context.

### Current Limitations

| Aspect | Current State | Problem |
|--------|--------------|---------|
| **Schema** | Fixed, predefined extraction | Can't adapt to new domains |
| **Detection** | Hash + semantic diff | Programmatic, brittle |
| **Scheduling** | Fixed cron | Doesn't adapt to data volatility |
| **Query** | Static | Can't refine search strategy |
| **Output** | Notification only | Limits platform potential |

### Future Visions This Enables

**Vision 1: ToraleDB (Infinite API)**
- Web as queryable database
- Define schema → Torale populates continuously
- `SELECT * FROM Competitor_Pricing WHERE price < 100`

**Vision 2: Sensory Cortex for AI Agents**
- Torale becomes the "trigger layer" for AI ecosystem
- Efficient filtering that only wakes expensive LLMs when something changes
- You own the "When" of AI execution

**Vision 3: Alpha Marketplace**
- Experts create valuable monitoring signals
- Enterprises subscribe via API
- Structured intelligence as tradeable asset

**All three visions require the same foundation**: structured state as the core asset, not notifications as the end goal.

---

## What

### The Core Shift

Evolve from notification-centric to **intelligence-centric** architecture:

```
OLD:  Monitor → Detect Change → Notify
NEW:  Sense → Structure → Govern → Act (maybe)
```

| Current | New |
|---------|-----|
| Fixed schema extraction | LLM-generated, evolving domain-specific state |
| Hash + semantic diff | LLM reads state and decides |
| Fixed cron schedule | Adaptive scheduling (Governor decides) |
| Static search query | Query can evolve (anchored to original) |
| Notification as output | Structured state as the asset |

### Architecture: Sensor + Governor

Two decoupled components with persistence as the boundary:

```
            ┌─────────────┐
   Web ────►│   Sensor    │────► Structured State
            └─────────────┘              │
                                         ▼
                                    [Persist]
                                         │
            ┌─────────────┐              │
  Actions ◄─┤  Actuator   │◄───┬─────────┘
  (email,   └─────────────┘    │
   webhook,                    ▼
   agent)              ┌──────────┐
                       │ Governor │◄── Criteria
                       └──────────┘
                            │
                            ▼
                      Next Check
```

### Component Responsibilities

| Component | Role | Inputs | Outputs |
|-----------|------|--------|---------|
| **Sensor** | Perceive & structure | Query, previous state | Structured state, volatility hints |
| **Governor** | Decide & regulate | State, criteria | Should act?, action content, next check |
| **Actuator** | Execute | Action decision | Delivery (email, webhook, etc.) |

**Key insight**: Sensor is passive (gathers data). Governor is active (controls behavior).

### Why This Split?

**Sensor** answers: "What's happening in the world?"
- Factual, objective
- Transforms unstructured web → structured knowledge
- Reports volatility signals ("event in 3 days", "data stale")

**Governor** answers: "What should we do about it?"
- Evaluative, criteria-based
- Decides if action warranted
- Decides when to sense again
- Could be rules-based OR LLM-based depending on complexity

**Actuator** answers: "How do we deliver?"
- Pure infrastructure
- Multiple channels (email, webhook, agent trigger)
- Already decoupled in current system

### The Deconstructed Agent Loop

Traditional agent loops run continuously. Ours is deconstructed:

```
┌─────────────────────────────────────────────────────────┐
│                    AGENT LOOP                           │
│         (deconstructed - one iteration at a time)       │
│                                                         │
│   Schedule ──► Sense ──► Persist ──► Govern ──► Act     │
│      ▲                                    │             │
│      │                                    │             │
│      └──────────── next_check ◄───────────┘             │
└─────────────────────────────────────────────────────────┘
```

Each scheduled run = one iteration. State persists between runs. Governor decides when to run next.

### Temporal Workflow

```python
@workflow.defn
class MonitorWorkflow:
    @workflow.run
    async def run(self, task_id: str) -> dict:
        # 1. Load context
        context = await workflow.execute_activity(
            "load_sensor_context",
            args=[task_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 2. Sense (web → structured state)
        sensor_output = await workflow.execute_activity(
            "sense",
            args=[context],
            start_to_close_timeout=timedelta(minutes=5),
        )

        # 3. Persist state
        await workflow.execute_activity(
            "save_state",
            args=[task_id, sensor_output],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 4. Govern (decide action + scheduling)
        decision = await workflow.execute_activity(
            "govern",
            args=[task_id, sensor_output],
            start_to_close_timeout=timedelta(minutes=1),
        )

        # 5. Act if needed
        if decision["should_act"]:
            await workflow.execute_activity(
                "execute_action",
                args=[task_id, decision],
                start_to_close_timeout=timedelta(minutes=1),
            )

        # 6. Schedule next check
        await workflow.execute_activity(
            "schedule_next_check",
            args=[task_id, decision["next_check"]],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {"sensor_output": sensor_output, "decision": decision}
```

### Data Models

```python
from pydantic import BaseModel, Field

# Sensor models
class SensorContext(BaseModel):
    """Input to sensor."""
    original_query: str
    current_query: str
    previous_state: str
    run_count: int


class SensorOutput(BaseModel):
    """Output from sensor."""
    updated_state: str = Field(description="Structured state (replaces old)")
    volatility_hint: str | None = Field(default=None, description="Data freshness signal")
    query_update: str | None = Field(default=None, description="Refined search query")
    error: str | None = None


# Governor models
class GovernorContext(BaseModel):
    """Input to governor."""
    original_query: str
    notification_criteria: str
    previous_state: str
    current_state: str
    volatility_hint: str | None
    run_count: int


class GovernorDecision(BaseModel):
    """Output from governor."""
    should_act: bool = Field(description="Whether to take action")
    action_type: str | None = Field(default=None, description="notify, webhook, agent_trigger")
    action_content: str | None = Field(default=None, description="Content for action")
    next_check: str = Field(description="When to sense again, e.g. '6 hours'")
    reasoning: str | None = Field(default=None, description="Why this decision")
```

### State Management

State lives in `tasks.last_known_state` JSONB column.

**System fields (fixed):**
```python
{
    "original_query": str,        # Immutable
    "current_query": str,         # May evolve (sensor updates)
    "notification_criteria": str, # What triggers action
    "run_count": int,
    "last_run_at": datetime,
}
```

**Domain-specific state (Sensor-managed):**

The sensor creates and maintains structured knowledge relevant to the monitoring task:

| Monitoring Query | State Shape |
|-----------------|-------------|
| iPhone 16 release | `{announced: bool, release_date: str?, pricing: str?}` |
| Protocol updates | `{latest_version: str, breaking_changes: []}` |
| Competitor pricing | `{products: [{sku, price, last_seen}]}` |

This IS the asset. Notification is just one way to consume it.

---

## How

### Implementation Options

We have two paths for LLM calls: ADK (Google's Agent Development Kit) or LangChain with native Gemini.

#### Option 1: ADK (Recommended for Sensor)

ADK supports `output_schema` + `tools` (like google_search):

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

def create_sensor(model: str = "gemini-2.5-flash") -> LlmAgent:
    """Factory function for sensor agent."""
    return LlmAgent(
        name="sensor",
        model=model,
        description="Perceives the web and structures findings",
        instruction=SENSOR_PROMPT,
        tools=[google_search],
        output_schema=SensorOutput,
        output_key="sensor_output",
    )
```

**Running the sensor:**

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def sense(context: SensorContext) -> SensorOutput:
    """Run sensor agent."""
    agent = create_sensor()
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="torale",
        session_service=session_service
    )

    session = await session_service.create_session(
        app_name="torale",
        user_id="system",
    )

    prompt = build_sensor_prompt(context)
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(prompt)]
    )

    async for event in runner.run_async(
        user_id="system",
        session_id=session.id,
        new_message=content
    ):
        pass

    output_data = session.state.get("sensor_output")
    return SensorOutput.model_validate_json(output_data)
```

#### Option 2: LangChain with Native Gemini Grounding

For more control or LangSmith observability:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from google.genai.types import Tool, GoogleSearch, GenerateContentConfig

class LangChainSensor:
    """Sensor using LangChain + native Gemini grounding."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.genai_client = genai.Client(api_key=settings.google_api_key)
        self.search_tool = Tool(google_search=GoogleSearch())
        self.llm = ChatGoogleGenerativeAI(model=model)
        self.structured_llm = self.llm.with_structured_output(SensorOutput)

    async def _grounded_search(self, query: str) -> str:
        """Native Gemini grounded search."""
        response = await self.genai_client.aio.models.generate_content(
            model=self.model,
            contents=query,
            config=GenerateContentConfig(
                tools=[self.search_tool],
                response_modalities=["TEXT"],
            ),
        )
        return response.text

    async def sense(self, context: SensorContext) -> SensorOutput:
        """Run sensor."""
        search_results = await self._grounded_search(context.current_query)

        chain = self.prompt | self.structured_llm
        return await chain.ainvoke({
            "original_query": context.original_query,
            "previous_state": context.previous_state or "(first check)",
            "current_query": context.current_query,
            "run_count": context.run_count,
            "search_results": search_results,
        })
```

#### Governor Implementation

Governor doesn't need search - it just reasons about state:

```python
class Governor:
    """Evaluates state and decides action + scheduling."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model)
        self.structured_llm = self.llm.with_structured_output(GovernorDecision)

        self.prompt = ChatPromptTemplate.from_template("""You are a monitoring governor.

## Mission
{original_query}

## Action Criteria
{notification_criteria}

## Previous State
{previous_state}

## Current State (just sensed)
{current_state}

## Volatility Signal
{volatility_hint}

## Instructions
1. Compare previous and current state
2. Decide if action criteria are met
3. Determine appropriate action type if needed
4. Decide when to sense again based on:
   - Volatility hint from sensor
   - Urgency of the monitoring task
   - Whether we just took action

Return your decision.""")

    async def govern(self, context: GovernorContext) -> GovernorDecision:
        """Evaluate and decide."""
        chain = self.prompt | self.structured_llm
        return await chain.ainvoke({
            "original_query": context.original_query,
            "notification_criteria": context.notification_criteria,
            "previous_state": context.previous_state or "(first run)",
            "current_state": context.current_state,
            "volatility_hint": context.volatility_hint or "(no hint)",
        })
```

**Note**: Governor could also be rules-based for simple criteria:

```python
def simple_governor(context: GovernorContext) -> GovernorDecision:
    """Rules-based governor for simple cases."""
    # Parse state changes, apply simple rules
    # Fallback to LLM for complex criteria
    pass
```

### Sensor Prompt

```python
SENSOR_PROMPT = """You are a web sensor for a monitoring system.

## Your Mission
{original_query}

## What You Know (from previous sensing)
{previous_state}

## Current Search Query
{current_query}

## Run Information
This is sensing run #{run_count}.

## Instructions

1. Search for current information using google_search
2. Structure your findings into domain-relevant state
   - What fields are important to track for this topic?
   - Update values based on what you find
3. Note any volatility signals:
   - Is this data changing rapidly?
   - Are there upcoming events/dates?
   - How fresh is the information?
4. Optionally refine the search query if you think a different angle would work better
   (stay true to the original mission)

Return your structured findings. You are sensing, not deciding - the Governor will interpret your output."""
```

### Scheduling

Governor decides `next_check`. The system parses and applies bounds:

```python
def parse_next_check(hint: str) -> timedelta:
    """Parse governor's scheduling hint."""
    # "6 hours" → timedelta(hours=6)
    # "2 days" → timedelta(days=2)
    # Apply bounds
    MIN_CHECK = timedelta(minutes=15)
    MAX_CHECK = timedelta(days=30)
    DEFAULT = timedelta(hours=24)

    parsed = _parse_duration(hint)  # Implementation details
    return max(MIN_CHECK, min(MAX_CHECK, parsed or DEFAULT))
```

### File Structure

```
backend/src/torale/
├── agentic/
│   ├── __init__.py
│   ├── sensor.py          # Sensor agent (ADK or LangChain)
│   ├── governor.py        # Governor logic
│   ├── models.py          # SensorOutput, GovernorDecision, etc.
│   ├── prompts.py         # Prompt templates
│   └── scheduling.py      # next_check parsing
├── workers/
│   ├── workflows.py       # Temporal workflow
│   └── activities.py      # Temporal activities
```

### Dependencies

```toml
# pyproject.toml

[project.dependencies]
google-adk = ">=0.1.0"
google-genai = ">=0.5.0"

[project.optional-dependencies]
langchain = [
    "langchain>=0.3",
    "langchain-google-genai>=2.0",
]
```

---

## Design Principles

### State is the Asset

Build around structured state, not around notifications:
- Sensor produces the asset (structured knowledge)
- Governor and Actuator consume it
- Future consumers: API, Dashboard, Marketplace, Agent Triggers

### Single Responsibility

| Component | Does | Doesn't |
|-----------|------|---------|
| Sensor | Perceive, structure | Decide actions |
| Governor | Evaluate, schedule | Search the web |
| Actuator | Deliver | Decide what to send |

### Extension Points

```
SensorOutput model  → Add fields for new domains
Governor            → Swap LLM for rules, or vice versa
Actuator            → Add new channels (SMS, Slack, agent trigger)
Scheduling          → Swap Temporal for DB-based polling
```

### Start Simple, Extend Later

Not implemented on day 1 (but designed for):
- State compression (when state grows too large)
- Query guardrails (if drift observed)
- Multi-action routing (different actuators per task)
- Marketplace exposure (state as API)

---

## Migration Strategy

### Phase 1: Parallel Implementation

- Build agentic system alongside existing
- New tasks can opt-in
- Existing tasks unchanged

### Phase 2: Migration

- Migrate existing tasks
- Convert `last_known_state` to new schema
- Initial state = LLM summary of old structured extraction

### Phase 3: Cleanup

- Remove old pipeline (SchemaProvider, ExtractionProvider, ComparisonProvider)
- Remove hash pre-filter

---

## Open Questions

See `agentic-plan-clarifications.md` for resolved items and remaining details.
