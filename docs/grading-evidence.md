# Evidence Collection Sheet

## Required screenshots — ĐÃ ĐỦ ✓

- [x] Langfuse trace list với ≥ 10 traces → `docs/screenshots/langfuse_trace_list.png` (214 traces)
- [x] One full trace waterfall → `docs/screenshots/Specific_trace_in_langfuse.png`
- [x] JSON logs showing correlation_id → `docs/screenshots/Validate_logs.png`
- [x] Log line với PII redaction → `docs/screenshots/PII_Injection.png`
- [x] Dashboard với 6 panels → `docs/screenshots/01_dashboard_normal.png`
- [x] Alert rules với runbook link → `config/alert_rules.yaml` + `docs/alerts.md`

## Optional screenshots — ĐÃ ĐỦ ✓

- [x] Incident before/after fix → `docs/screenshots/before_and_after_ragSlow.png`, `docs/screenshots/Dashboard_Slow_Rag.png`
- [x] Cost comparison (normal vs cost_spike) → `docs/screenshots/estimate100.png`
- [x] Audit log proof → `data/audit.jsonl` (254 entries, committed `abdda78`)

## Validate logs score

- VALIDATE_LOGS_FINAL_SCORE: 100/100
- TOTAL_TRACES_COUNT: 214
- PII_LEAKS_FOUND: 0
