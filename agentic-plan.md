# Torale Agentic Evolution Plan

## Why

### The Problem

Torale currently operates as a **notification tool**: monitor → detect change → alert. But notifications are ephemeral. The real value is the **structured intelligence** extracted from the chaotic web.

> **Core Insight**: You built a "change detection engine for reality" but are boxing it in as a "notification tool." Notifications are ephemeral; **Intelligence is an asset.**

See [Product Vision Discussion](https://github.com/prassanna-ravishankar/torale/issues/121#issuecomment-3650006660) for full context.

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
- Own the "When" of AI execution

**Vision 3: Alpha Marketplace**
- Experts create valuable monitoring signals
- Enterprises subscribe via API
- Structured intelligence as tradeable asset

**All three require the same foundation**: structured state as the core asset, not notifications as the end goal.

---

## What

### The Core Shift

From notification-centric to **intelligence-centric** architecture:

```
OLD:  Monitor → Detect Change → Notify
NEW:  Sense → Structure → Govern → Act (maybe)
```

| Current | New |
|---------|-----|
| Fixed schema extraction | LLM-generated, evolving domain-specific state |
| Hash + semantic diff | Governor reads state and decides |
| Fixed cron schedule | Adaptive scheduling (Governor decides) |
| Static search query | Query can evolve (Sensor refines) |
| Notification as output | Structured state as the asset |

### Architecture: Sensor + Governor

Two decoupled components. Persistence is the boundary.

```
┌─────────────────────────────────────────────────────────────┐
│                         FLOW                                 │
│                                                              │
│   ┌────────┐      ┌─────────┐      ┌──────────┐             │
│   │ Sensor │ ───► │ Persist │ ───► │ Governor │             │
│   └────────┘      └─────────┘      └──────────┘             │
│        │                                 │                   │
│        │                                 ▼                   │
│        │                          ┌──────────┐              │
│        │                          │ Actuator │──► Actions   │
│        │                          └──────────┘   (email,    │
│        │                                 │        webhook,  │
│        │                                 │        agent)    │
│        │                                 ▼                   │
│        │                           next_check                │
│        │                                 │                   │
│        └─────────────────────────────────┘                   │
│                    (scheduled)                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Question | Inputs | Outputs |
|-----------|----------|--------|---------|
| **Sensor** | "What's happening?" | Query, previous state | Structured state, volatility hint |
| **Governor** | "What should we do?" | States (prev + current), criteria | Should act?, action content, next check |
| **Actuator** | "How do we deliver?" | Action decision | Delivery (email, webhook, etc.) |

**Key insight**: Sensor is passive (perceives). Governor is active (controls).

### Why This Split?

**Sensor** (passive, factual):
- Transforms unstructured web → structured knowledge
- Reports volatility signals ("event in 3 days", "data seems stale")
- May refine search query for better results
- Does NOT decide whether to act

**Governor** (active, evaluative):
- Compares previous state vs current state
- Evaluates against action criteria
- Decides if action is warranted
- Decides when to sense again (using sensor's volatility hint)
- Could be LLM-based OR rules-based

**Actuator** (infrastructure):
- Executes the Governor's decision
- Multiple channels: email, webhook, agent trigger, API
- Already exists in current system

### The Deconstructed Agent Loop

Traditional agents run continuously. Ours is deconstructed:

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

### Data Models

```python
from pydantic import BaseModel, Field

# === Sensor Models ===

class SensorContext(BaseModel):
    """What sensor needs to do its job."""
    original_query: str      # The mission (immutable)
    current_query: str       # May have been refined
    previous_state: str      # What we knew before
    run_count: int


class SensorOutput(BaseModel):
    """What sensor produces."""
    updated_state: str = Field(
        description="Structured state representing current knowledge"
    )
    volatility_hint: str | None = Field(
        default=None,
        description="Signal about data freshness: 'changing rapidly', 'event in 3 days', etc."
    )
    query_update: str | None = Field(
        default=None,
        description="Refined search query if sensor thinks a different approach works better"
    )
    error: str | None = None


# === Governor Models ===

class GovernorContext(BaseModel):
    """What governor needs to make decisions."""
    original_query: str      # The mission
    action_criteria: str     # When to act (user-defined)
    previous_state: str      # Before this sensing
    current_state: str       # After this sensing (from sensor)
    volatility_hint: str | None  # From sensor
    run_count: int


class GovernorDecision(BaseModel):
    """What governor decides."""
    should_act: bool = Field(
        description="Whether action criteria are met"
    )
    action_type: str | None = Field(
        default=None,
        description="Type of action: 'email', 'webhook', 'agent_trigger'"
    )
    action_content: str | None = Field(
        default=None,
        description="Content/payload for the action"
    )
    next_check: str = Field(
        description="When to sense again: '6 hours', '2 days', etc."
    )
    reasoning: str | None = Field(
        default=None,
        description="Why this decision was made"
    )
```

### State Schema

State lives in `tasks.last_known_state` JSONB column.

**System fields (fixed structure):**
```python
{
    "original_query": str,     # Immutable - the mission
    "current_query": str,      # May evolve (sensor refines)
    "action_criteria": str,    # When to act
    "state_summary": str,      # Domain-specific structured state
    "run_count": int,
    "last_run_at": datetime,
}
```

**Domain-specific state (Sensor-managed):**

The `state_summary` contains structured knowledge. Sensor decides what's relevant:

| Monitoring Query | State Shape |
|-----------------|-------------|
| iPhone 17 release | `{announced: bool, date: "TBD", pricing: null, rumored_features: [...]}` |
| Protocol updates | `{version: "2.1.0", released: "2024-01-15", breaking_changes: [...]}` |
| Competitor pricing | `{products: [{sku: "X", price: 99, last_seen: "..."}]}` |

This IS the asset. Actions are just one way to consume it.

### Temporal Workflow

```python
from datetime import timedelta
from temporalio import workflow

@workflow.defn
class MonitorWorkflow:
    @workflow.run
    async def run(self, task_id: str) -> dict:
        # 1. Load task state from DB
        task_state = await workflow.execute_activity(
            "load_task_state",
            args=[task_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 2. Build sensor context
        sensor_context = SensorContext(
            original_query=task_state["original_query"],
            current_query=task_state["current_query"],
            previous_state=task_state["state_summary"],
            run_count=task_state["run_count"],
        )

        # 3. Sense (web → structured state)
        sensor_output = await workflow.execute_activity(
            "sense",
            args=[sensor_context.model_dump()],
            start_to_close_timeout=timedelta(minutes=5),
        )

        # 4. Persist state immediately (state is the asset)
        await workflow.execute_activity(
            "save_state",
            args=[task_id, sensor_output],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 5. Build governor context
        governor_context = GovernorContext(
            original_query=task_state["original_query"],
            action_criteria=task_state["action_criteria"],
            previous_state=task_state["state_summary"],
            current_state=sensor_output["updated_state"],
            volatility_hint=sensor_output.get("volatility_hint"),
            run_count=task_state["run_count"],
        )

        # 6. Govern (decide action + scheduling)
        decision = await workflow.execute_activity(
            "govern",
            args=[governor_context.model_dump()],
            start_to_close_timeout=timedelta(minutes=1),
        )

        # 7. Act if needed
        if decision["should_act"]:
            await workflow.execute_activity(
                "execute_action",
                args=[task_id, decision],
                start_to_close_timeout=timedelta(minutes=1),
            )

        # 8. Schedule next sensing
        await workflow.execute_activity(
            "schedule_next_check",
            args=[task_id, decision["next_check"]],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {
            "sensor_output": sensor_output,
            "decision": decision,
        }
```

### Activities

| Activity | What it does |
|----------|-------------|
| `load_task_state` | Load task + state from PostgreSQL |
| `sense` | Run Sensor (LLM + google_search) |
| `save_state` | Persist sensor output to `last_known_state` |
| `govern` | Run Governor (LLM or rules) |
| `execute_action` | Dispatch via Actuator (email, webhook, etc.) |
| `schedule_next_check` | Update Temporal schedule for next run |

---

## How

### Sensor Implementation

Sensor needs google_search grounding. Two options:

#### Option A: ADK (Google's Agent Development Kit)

```python
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

SENSOR_PROMPT = """You are a web sensor for a monitoring system.

## Mission
{original_query}

## Previous Knowledge
{previous_state}

## Current Search Query
{current_query}

## Run #{run_count}

## Instructions
1. Search using google_search to find current information
2. Structure findings into domain-relevant state
   - What fields matter for this topic?
   - What are the current values?
3. Note volatility signals:
   - Is data changing rapidly?
   - Any upcoming events/dates?
   - How fresh is the information?
4. Optionally refine the query if a different angle works better

You are sensing, not deciding. Governor will interpret your output."""


def create_sensor(model: str = "gemini-2.5-flash") -> LlmAgent:
    return LlmAgent(
        name="sensor",
        model=model,
        description="Perceives the web and structures findings",
        instruction=SENSOR_PROMPT,
        tools=[google_search],
        output_schema=SensorOutput,
        output_key="sensor_output",
    )


async def sense(context: SensorContext) -> SensorOutput:
    """Run sensor agent."""
    agent = create_sensor()
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="torale",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="torale",
        user_id="system",
    )

    prompt = SENSOR_PROMPT.format(
        original_query=context.original_query,
        previous_state=context.previous_state or "(first sensing)",
        current_query=context.current_query,
        run_count=context.run_count,
    )

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(prompt)],
    )

    async for event in runner.run_async(
        user_id="system",
        session_id=session.id,
        new_message=content,
    ):
        pass  # Stream through events

    output_data = session.state.get("sensor_output")
    return SensorOutput.model_validate_json(output_data)
```

#### Option B: LangChain + Native Gemini Grounding

```python
from google import genai
from google.genai.types import Tool, GoogleSearch, GenerateContentConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


class LangChainSensor:
    """Sensor using LangChain with native Gemini grounding."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.genai_client = genai.Client(api_key=settings.google_api_key)
        self.search_tool = Tool(google_search=GoogleSearch())

        self.llm = ChatGoogleGenerativeAI(model=model)
        self.structured_llm = self.llm.with_structured_output(SensorOutput)

        self.prompt = ChatPromptTemplate.from_template("""You are a web sensor.

## Mission
{original_query}

## Previous Knowledge
{previous_state}

## Search Results
{search_results}

## Run #{run_count}

Structure these findings. Note any volatility signals. You sense, you don't decide.""")

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
        search_results = await self._grounded_search(context.current_query)

        chain = self.prompt | self.structured_llm
        return await chain.ainvoke({
            "original_query": context.original_query,
            "previous_state": context.previous_state or "(first sensing)",
            "search_results": search_results,
            "run_count": context.run_count,
        })
```

### Governor Implementation

Governor doesn't need search. It reasons about state.

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

GOVERNOR_PROMPT = """You are a monitoring governor.

## Mission
{original_query}

## Action Criteria
{action_criteria}

## Previous State
{previous_state}

## Current State (just sensed)
{current_state}

## Volatility Signal
{volatility_hint}

## Instructions
1. Compare previous and current state
2. Decide if action criteria are met
3. If acting, determine action type and content
4. Decide when to sense again:
   - Consider volatility hint
   - Consider urgency of the mission
   - Consider whether we just acted

Return your decision."""


class Governor:
    """Evaluates state and decides action + scheduling."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model)
        self.structured_llm = self.llm.with_structured_output(GovernorDecision)
        self.prompt = ChatPromptTemplate.from_template(GOVERNOR_PROMPT)

    async def govern(self, context: GovernorContext) -> GovernorDecision:
        chain = self.prompt | self.structured_llm
        return await chain.ainvoke({
            "original_query": context.original_query,
            "action_criteria": context.action_criteria,
            "previous_state": context.previous_state or "(first run)",
            "current_state": context.current_state,
            "volatility_hint": context.volatility_hint or "(no signal)",
        })
```

**Alternative: Rules-based Governor**

For simple criteria, skip the LLM:

```python
def simple_governor(context: GovernorContext) -> GovernorDecision:
    """Rules-based governor for simple cases."""
    prev = json.loads(context.previous_state) if context.previous_state else {}
    curr = json.loads(context.current_state)

    # Example: notify when "announced" changes to True
    should_act = curr.get("announced") and not prev.get("announced")

    return GovernorDecision(
        should_act=should_act,
        action_type="email" if should_act else None,
        action_content=f"Announcement detected: {curr}" if should_act else None,
        next_check="6 hours" if curr.get("announced") else "1 day",
    )
```

### Scheduling

Governor outputs `next_check` as natural language. System parses and bounds it:

```python
from datetime import timedelta
import re

MIN_CHECK = timedelta(minutes=15)
MAX_CHECK = timedelta(days=30)
DEFAULT_CHECK = timedelta(hours=24)


def parse_next_check(hint: str) -> timedelta:
    """Parse '6 hours', '2 days', etc. into timedelta."""
    patterns = [
        (r"(\d+)\s*min", lambda m: timedelta(minutes=int(m.group(1)))),
        (r"(\d+)\s*hour", lambda m: timedelta(hours=int(m.group(1)))),
        (r"(\d+)\s*day", lambda m: timedelta(days=int(m.group(1)))),
        (r"(\d+)\s*week", lambda m: timedelta(weeks=int(m.group(1)))),
    ]

    for pattern, converter in patterns:
        match = re.search(pattern, hint.lower())
        if match:
            delta = converter(match)
            return max(MIN_CHECK, min(MAX_CHECK, delta))

    return DEFAULT_CHECK
```

### File Structure

```
backend/src/torale/agentic/
├── __init__.py
├── models.py          # SensorContext, SensorOutput, GovernorContext, GovernorDecision
├── sensor.py          # Sensor implementations (ADK, LangChain)
├── governor.py        # Governor implementations (LLM, rules-based)
├── prompts.py         # SENSOR_PROMPT, GOVERNOR_PROMPT
├── scheduling.py      # parse_next_check, bounds
└── workflow.py        # MonitorWorkflow, activities
```

### Dependencies

```toml
# pyproject.toml

[project.dependencies]
google-adk = ">=0.1.0"
google-genai = ">=0.5.0"
langchain-google-genai = ">=2.0.0"
temporalio = ">=1.0.0"
pydantic = ">=2.0.0"
```

---

## Design Principles

### State is the Asset

- Sensor produces the asset (structured knowledge)
- Governor and Actuator consume it
- Future consumers: API, Dashboard, Marketplace, Agent Triggers
- Persist state BEFORE governing (state matters even if action fails)

### Single Responsibility

| Component | Does | Does NOT |
|-----------|------|----------|
| Sensor | Perceive, structure, hint volatility | Decide actions |
| Governor | Evaluate, decide, schedule | Search the web |
| Actuator | Deliver actions | Decide what to send |

### Extension Points

| What | How |
|------|-----|
| New domains | Sensor adapts state structure automatically |
| New action types | Add to Actuator (SMS, Slack, agent trigger) |
| Complex criteria | Swap rules-based Governor for LLM-based |
| Simple criteria | Swap LLM-based Governor for rules-based |
| Different scheduling | Swap Temporal for DB-polling |

### Start Simple, Extend Later

Designed for but NOT implemented day 1:
- State compression (when state grows too large)
- Query guardrails (if drift from original mission)
- Multi-action routing (different actuators per task)
- Marketplace exposure (state as API endpoint)

---

## Migration Strategy

### Phase 1: Parallel

- Build agentic system alongside existing
- New tasks opt-in to agentic mode
- Existing tasks unchanged

### Phase 2: Migrate

- Convert existing tasks to agentic
- Transform `last_known_state` to new schema
- Initial `state_summary` = LLM summary of old structured data

### Phase 3: Cleanup

- Remove old pipeline (SchemaProvider, ExtractionProvider, ComparisonProvider)
- Remove hash-based pre-filter

---

## Open Questions

See `agentic-plan-clarifications.md` for resolved items and remaining details.
