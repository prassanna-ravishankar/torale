# Agentic Plan - Research & Deferred Items

## ADK Research Summary

Validated approach against ADK docs. Key findings:

1. **`output_schema` + `tools` works** - ADK adds `set_model_response` tool internally. Perfect for google_search + Observation schema.

2. **`output_key` saves to session state** - `session.state[output_key]` contains the Observation.

3. **`Runner.run_async` is primary** - Async-first.

4. **`InMemorySessionService` for ephemeral** - We persist state in PostgreSQL, not ADK.

### References

- [output_schema with tools sample](https://github.com/google/adk-python/blob/main/contributing/samples/output_schema_with_tools/README.md)
- [LlmAgent structured output docs](https://google.github.io/adk-docs/agents/llm-agents/#structuring-data-input-schema-output-schema-output-key)
- [Session management](https://google.github.io/adk-docs/sessions/session/)
- [Runtime / Runner](https://google.github.io/adk-docs/runtime/)
- [Google Search grounding](https://google.github.io/adk-docs/grounding/google_search_grounding/)

---

## Deferred to Implementation

These items will be figured out during implementation:

| Item | Notes |
|------|-------|
| State summary format | Structured or prose - let LLM decide |
| Grounding source handling | Keep current behavior |
| Testing strategy | Mock ADK for workflow tests, real integration for happy path |
| Cost tracking | Continue existing, add limits later if needed |
| Migration of existing tasks | Defer until new system works |
| Notify behavior compat | Include as context in prompt, LLM respects it |

---

## Not Implementing Yet

Add later when needed:

- **Compression** - Enable via settings when state actually gets large
- **Query guardrails** - Add if drift becomes a problem
- **Confidence-based logic** - Log only, don't act on it
- **Multi-agent structure** - Factory allows swap later
- **UI updates** - Backend first
