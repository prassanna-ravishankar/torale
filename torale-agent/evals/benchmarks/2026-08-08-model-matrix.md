# Monitoring model matrix — 2026-08-08

## Decision

Use Gemini 3.5 Flash-Lite with `minimal` thinking for the webwhen monitoring
agent. It matched the higher thinking levels on the reviewed decision cases
while completing in less than half the time of `medium` and `high`.

Keep GPT-OSS 120B as a low-cost candidate, not the primary model yet. It made
the right trigger decision in every scored run, but missed the required search
step once and showed materially higher latency variance. Gemma 4 is not suitable
for the grounded agent in its current configuration because it repeatedly
answered from model knowledge without calling a search tool.

## Method

- Dataset: the four durable trigger/no-trigger cases in `evals/cases.yaml`.
- Agent: the production prompt, tools, dependencies, retries, and structured
  `MonitoringResponse` contract.
- Assertions: trigger decision, search use, sources when notifying, and a future
  `next_run`.
- Gemini finalist configurations and GPT-OSS were run 12 times each (three runs
  of each case). Other configurations received one four-case screening pass.
- Calls were sequential and used the paid Gemini key to avoid free-tier request
  limits. Open models used the Agent Platform global MaaS endpoint.
- Cost estimates include model tokens only. Search, memory, and other tool costs
  are excluded.

## Screening pass

| Configuration | Decisions | Searches | Mean latency | Model cost |
|---|---:|---:|---:|---:|
| Gemini 3.5 Flash-Lite minimal | 4/4 | 4/4 | 6.6s | $0.0490 |
| Gemini 3.5 Flash-Lite low | 4/4 | 4/4 | 7.1s | $0.0531 |
| Gemini 3.5 Flash-Lite medium | 4/4 | 4/4 | 11.9s | $0.0433 |
| Gemini 3.5 Flash-Lite high | 4/4 | 4/4 | 14.0s | $0.0593 |
| Gemma 4 26B A4B IT | 3/4 | 0/4 | 4.1s | $0.0022 |
| GPT-OSS 120B | 4/4 | 4/4 | 9.0s | $0.0061 |

## Finalist repetitions

The totals below combine the screening pass with two additional repetitions of
each case.

| Configuration | Decisions | Searches | Mean latency | Model cost | Cost/run |
|---|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash-Lite minimal | 12/12 | 12/12 | 6.3s | $0.1506 | $0.0125 |
| Gemini 3.5 Flash-Lite medium | 12/12 | 12/12 | 12.4s | $0.1478 | $0.0123 |
| GPT-OSS 120B | 12/12 | 11/12 | 14.1s | $0.0230 | $0.0019 |

GPT-OSS also had one structured-output retry exhaustion during an earlier
concurrent spike. That run is not included in the finalist table because the
spike used a broken result collector, but the model failure itself was genuine
and should remain part of the reliability assessment.

## Harness findings

- Pydantic AI's generic `openai:` identifier selects the Responses API. Agent
  Platform open-model MaaS requires the explicit `openai-chat:` provider.
- Open MaaS models need native JSON-schema output. GPT-OSS rejects the forced
  final-result tool used by Pydantic AI's default output mode.
- Pydantic AI 2.27's OpenAI provider requires OpenAI SDK 2.45 or newer; the old
  unconstrained direct dependency resolved to an incompatible SDK.
- The Gemini free key's 15 requests/minute limit is insufficient for a
  multi-turn matrix. Benchmarks should use the paid key or deliberately pace
  requests.

## Caveats and production monitoring

Four reviewed cases are enough to reject obvious protocol failures, not to
prove broad monitoring quality. After making `minimal` the production default:

1. Compare tool-use rate, task failures, trigger rate, latency, and token usage
   against the pre-change `high` baseline in Logfire.
2. Revert to `high` if grounded-search compliance regresses.
