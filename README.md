# Day 13 — Observability Lab

A fully-instrumented FastAPI AI agent demonstrating production-grade observability: structured logging, correlation ID propagation, PII scrubbing, distributed tracing (Langfuse), real-time metrics, SLOs, and alert rules.

---

## What this project demonstrates

| Layer | Implementation |
|---|---|
| **Structured Logging** | `structlog` writes JSON lines to `data/logs.jsonl`; every log automatically carries `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model` |
| **Correlation IDs** | `CorrelationIdMiddleware` generates `req-<8hex>` per request (or echoes client-provided `x-request-id`), propagated to all logs and response headers |
| **PII Scrubbing** | Regex-based scrubber removes emails, Vietnamese phone numbers, CCCD, credit cards, passports, addresses, and bank account numbers before writing logs |
| **Audit Logging** | Separate `data/audit.jsonl` captures who-did-what for compliance; callers hash PII before writing |
| **Distributed Tracing** | Langfuse v3 `@observe()` decorator wraps the agent pipeline; traces include user hash, session, tags, and token usage |
| **Metrics** | In-memory windowed metrics (last 30 s): p50/p95/p99 latency, avg/total cost, token counts, quality score, error breakdown |
| **Dashboard** | Live HTML dashboard at `/dashboard` polls `/metrics` every 3 s and renders 6 panels |
| **SLOs** | Defined in `config/slo.yaml`: latency p95 < 2 s, error rate < 1%, daily cost < $2, quality avg ≥ 0.70 |
| **Alert Rules** | Defined in `config/alert_rules.yaml`: 4 rules (P1/P2) with runbook links |
| **Incident Injection** | Three toggleable failure modes to stress-test observability in real time |

---

## Architecture

```
POST /chat
     │
     ▼
CorrelationIdMiddleware        — generates x-request-id, binds to structlog context
     │
     ▼
chat() endpoint (main.py)      — binds user/session/feature to context, calls agent
     │
     ▼
LabAgent.run()  @observe()     — Langfuse trace wraps entire pipeline
  ├── mock_rag.retrieve()      — keyword search over CORPUS (can inject: rag_slow, tool_fail)
  ├── FakeLLM.generate()       — deterministic response (can inject: cost_spike)
  ├── metrics.record_request() — updates in-memory windowed stats
  └── langfuse_context.update_current_trace()
     │
     ▼
Structured log → data/logs.jsonl   (PII scrubbed)
Audit log      → data/audit.jsonl  (hashed IDs)
Response       → ChatResponse (includes correlation_id, latency_ms, cost_usd, quality_score)
```

---

## Quick start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and fill in Langfuse keys (optional — app runs without them in no-op mode):

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. Run

```bash
uvicorn app.main:app --reload
```

The app starts at `http://127.0.0.1:8000`.

| Endpoint | Purpose |
|---|---|
| `GET /health` | System status + active incidents |
| `GET /metrics` | Live metrics snapshot |
| `GET /dashboard` | HTML dashboard (6 panels) |
| `POST /chat` | Main agent endpoint |
| `POST /incidents/{name}/enable` | Inject a failure scenario |
| `POST /incidents/{name}/disable` | Restore normal operation |

---

## Demo scenario

The demo is structured in **4 acts** (~15 minutes total). Open the following in separate terminals before starting:

- **Terminal 1** — app server
- **Terminal 2** — load test / incident injection
- **Browser** — `http://127.0.0.1:8000/dashboard`
- **Browser tab 2** — Langfuse dashboard (if configured)

---

### Act 1 — Normal operation (3 min)

**Goal:** Show the system is healthy and all observability layers are working.

**Step 1** — Start the server and verify health:
```bash
curl http://127.0.0.1:8000/health
# Expected: {"ok": true, "tracing_enabled": true/false, "incidents": {"rag_slow": false, ...}}
```

**Step 2** — Send a batch of requests:
```bash
python scripts/load_test.py --concurrency 3
```

You will see output like:
```
[200] req-a1b2c3d4 | qa | 165.3ms
[200] req-f8e7d6c5 | summary | 171.2ms
```

**Step 3** — Open `http://127.0.0.1:8000/dashboard` in the browser.
- Confirm all 6 panels show data: traffic, latency p50/p95/p99, cost, tokens, quality score, error breakdown.
- Point out that p95 latency is well under the SLO threshold of **2000 ms**.

**Step 4** — Inspect a log entry:
```bash
tail -3 data/logs.jsonl | python -m json.tool
```
Show the audience: `correlation_id`, `user_id_hash` (not the raw user ID), `session_id`, `feature`, `model` are all present on every line automatically.

**Step 5** — Validate log schema:
```bash
python scripts/validate_logs.py
```
Expected: all required fields present, PII check passes (no raw emails or phone numbers in logs).

**Step 6** — (If Langfuse configured) Open Langfuse → Traces. Show ≥ 10 traces with tags `["lab", "qa", "claude-sonnet-4-5"]` and token usage.

---

### Act 2 — PII scrubbing in action (2 min)

**Goal:** Show that sensitive data never reaches the log file.

**Step 1** — Send a request containing PII in the message:
```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u_demo","session_id":"s_demo","feature":"qa","message":"My email is demo@test.com and phone is 0912345678, please check refund policy"}' \
  | python -m json.tool
```

**Step 2** — Check the log:
```bash
tail -1 data/logs.jsonl | python -m json.tool
```
Expected result: `"message_preview"` shows `[REDACTED_EMAIL]` and `[REDACTED_PHONE_VN]` instead of the real values. The raw PII never hit disk.

---

### Act 3 — Incident injection: RAG slowdown (5 min)

**Goal:** Simulate a real production incident, watch metrics degrade in real time, correlate with logs and traces.

**Step 1** — Enable the `rag_slow` incident (RAG now sleeps 2.5 s per request):
```bash
python scripts/inject_incident.py --scenario rag_slow
# or: curl -X POST http://127.0.0.1:8000/incidents/rag_slow/enable
```

**Step 2** — Run the load test again with higher concurrency:
```bash
python scripts/load_test.py --concurrency 5
```

**Step 3** — Watch the dashboard update in real time.
- p95 and p99 latency will spike from ~170 ms to **~2500 ms+**, crossing the SLO threshold (2000 ms).
- Point out that `alert_rules.yaml` defines `high_latency_p95: latency_p95_ms > 5000 for 30m → P2 page`.

**Step 4** — Show the log for a slow request:
```bash
tail -5 data/logs.jsonl | python -m json.tool
```
Notice `latency_ms` is now ~2600. The `correlation_id` on the log matches the one returned in the response — you can trace a single slow request end-to-end.

**Step 5** — (If Langfuse configured) Filter traces by the time window. The slow traces are visible with longer durations, same `session_id` and tags.

**Step 6** — Restore normal operation:
```bash
python scripts/inject_incident.py --scenario rag_slow --disable
```

Watch the dashboard: latency recovers within seconds. This demonstrates that metrics are windowed (last 30 s) so recovery is immediate and visible.

---

### Act 4 — Incident injection: error rate spike (3 min)

**Goal:** Show the error-rate alert path.

**Step 1** — Enable `tool_fail` (RAG raises `RuntimeError` on every call):
```bash
python scripts/inject_incident.py --scenario tool_fail
```

**Step 2** — Run load test:
```bash
python scripts/load_test.py --concurrency 3
```
All requests return HTTP 500. The terminal shows `[500]` responses.

**Step 3** — Check the dashboard: error breakdown panel now shows `RuntimeError` count rising. Narrate that `alert_rules.yaml` fires `high_error_rate: P1` at > 5% error rate sustained for 5 minutes.

**Step 4** — Show the error log:
```bash
grep '"level":"error"' data/logs.jsonl | tail -1 | python -m json.tool
```
The log captures `error_type`, `correlation_id`, and a scrubbed `message_preview` — enough to diagnose without exposing PII.

**Step 5** — Restore:
```bash
python scripts/inject_incident.py --scenario tool_fail --disable
```

---

### Closing (2 min)

Run the final validation and show everything passes:
```bash
python scripts/validate_logs.py
curl -s http://127.0.0.1:8000/metrics | python -m json.tool
```

Summary of what was shown:

| Observability layer | Demonstrated by |
|---|---|
| Correlation IDs | Every log and response carries the same `req-*` ID |
| Structured logs | JSON lines with full context, validated by `validate_logs.py` |
| PII scrubbing | Raw email/phone replaced before hitting disk |
| Tracing | Langfuse traces with user hash, session, tags, token usage |
| Metrics | Real-time windowed p50/p95/p99, cost, quality on dashboard |
| Incident response | RAG slow + tool_fail visible immediately in metrics and logs |
| SLOs & alerts | Defined thresholds map directly to observable metric values |

---

## Tooling reference

```bash
# Load test (default concurrency=1)
python scripts/load_test.py --concurrency 5

# Inject / restore incidents
python scripts/inject_incident.py --scenario rag_slow
python scripts/inject_incident.py --scenario rag_slow --disable
python scripts/inject_incident.py --scenario tool_fail
python scripts/inject_incident.py --scenario tool_fail --disable
python scripts/inject_incident.py --scenario cost_spike
python scripts/inject_incident.py --scenario cost_spike --disable

# Validate log schema and PII scrubbing
python scripts/validate_logs.py

# Run tests
pytest tests/ -v
```

Available incident scenarios:

| Scenario | Effect | Metric impact |
|---|---|---|
| `rag_slow` | RAG sleeps 2.5 s per call | latency p95/p99 spike |
| `tool_fail` | RAG raises RuntimeError | error rate spike, HTTP 500s |
| `cost_spike` | Token count × 4 | cost per request × 4 |

---

## Repo map

```
app/
  main.py              FastAPI app, endpoint handlers, context binding
  agent.py             Core pipeline: RAG → LLM → metrics + Langfuse trace
  logging_config.py    structlog configuration, PII scrub processor, audit logger
  middleware.py        CorrelationIdMiddleware — x-request-id generation & propagation
  pii.py               Regex scrubber (8 PII types) + hash_user_id
  tracing.py           Langfuse v3 integration with graceful fallback
  metrics.py           In-memory windowed metrics (30 s window, 5-entry buffer)
  incidents.py         Shared STATE dict + enable/disable/status helpers
  mock_llm.py          Deterministic fake LLM with token counting
  mock_rag.py          Keyword-based fake retrieval over 3-topic CORPUS
  schemas.py           Pydantic models: ChatRequest, ChatResponse, LogRecord
  dashboard.html       HTML dashboard with 6 metric panels (polls /metrics)
config/
  slo.yaml             4 SLIs with objectives and targets
  alert_rules.yaml     4 alert rules (P1/P2) with runbook links
  logging_schema.json  Expected log field schema
scripts/
  load_test.py         Concurrent request generator
  inject_incident.py   CLI to enable/disable incident scenarios
  validate_logs.py     Schema + PII compliance checker for data/logs.jsonl
data/
  sample_queries.jsonl Test requests
  logs.jsonl           Structured app log output
  audit.jsonl          Compliance audit trail
docs/
  blueprint-template.md  Team submission template
  alerts.md              Runbook + alert worksheet
  dashboard-spec.md      6-panel dashboard checklist
  grading-evidence.md    Evidence collection sheet
tests/
  test_middleware.py   Correlation ID middleware tests
  test_metrics.py      Percentile calculation tests
  test_pii.py          PII scrubber tests
```

---

## Grading policy (60/40 split)

1. **Group score (60%)**
   - Technical implementation (30 pts) — verified by `validate_logs.py` and live system
   - Incident response (10 pts) — root cause analysis accuracy in the report
   - Live demo (20 pts) — team presentation and system demonstration

2. **Individual score (40%)**
   - Individual report (20 pts) — contributions documented in `docs/blueprint-template.md`
   - Git evidence (20 pts) — traceable work via commits and code ownership

**Passing criteria**
- All TODO blocks completed
- Minimum 10 traces visible in Langfuse
- Dashboard shows all 6 required panels
