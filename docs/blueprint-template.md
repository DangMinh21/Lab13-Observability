# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Nhóm 9 — Day 13 Observability

- [REPO_URL]: [Link GitHub](https://github.com/DangMinh21/Lab13-Observability)

- [MEMBERS]:
  - Member A: Nguyễn Quang Tùng - 2A202600197 | Role: Correlation ID & Incident Debug
  - Member B: Nguyễn Thị Quỳnh Trang - 2A202600406 | Role: Logging & PII Scrubbing
  - Member C: Đặng Văn Minh - 2A202600027 | Role: Tracing (Langfuse) + SLO + Alerts
  - Member D: Đồng Văn Thịnh - 2A202600365 | Role: Dashboard + Docs + Report

---

## 2. Group Performance (Auto-Verified)
- VALIDATE_LOGS_FINAL_SCORE: 100/100
- TOTAL_TRACES_COUNT: 214
- PII_LEAKS_FOUND: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- EVIDENCE_CORRELATION_ID_SCREENSHOT: docs/screenshots/Validate_logs.png
- EVIDENCE_PII_REDACTION_SCREENSHOT: docs/screenshots/PII_Injection.png
- EVIDENCE_TRACE_WATERFALL_SCREENSHOT: docs/screenshots/Specific_trace_in_langfuse.png
- TRACE_WATERFALL_EXPLANATION: Span 'retrieve' thể hiện quá trình truy xuất dữ liệu từ vector database; là chìa khóa để chẩn đoán sự cố rag_slow.

### 3.2 Dashboard & SLOs
- DASHBOARD_NORMAL: [docs/screenshots/01_dashboard_normal.png](docs/screenshots/01_dashboard_normal.png)
- DASHBOARD_BREACH: [docs/screenshots/02_dashboard_breach.png](docs/screenshots/02_dashboard_breach.png)
- DASHBOARD_RECOVERED: [docs/screenshots/03_dashboard_recovered.png](docs/screenshots/03_dashboard_recovered.png)

- SLO_TABLE:

| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 2000ms | 28d | 164ms |
| Error Rate | < 2% | 28d | 0% |
| Cost Budget | < $1.0/day | 1d | $0.0118 |
| Quality Score Avg | ≥ 0.70 | 28d | 0.85 |

### 3.3 Alerting & Runbook
- DASHBOARD_6_PANELS_SCREENSHOT: [docs/screenshots/01_dashboard_normal.png](docs/screenshots/01_dashboard_normal.png)
- ALERT_RULES_SCREENSHOT: config/alert_rules.yaml (4 rules: high_latency_p95 P2, high_error_rate P1, cost_budget_spike P2, quality_score_degradation P2)
- SAMPLE_RUNBOOK_LINK: [docs/alerts.md#4-quality-score-degradation](docs/alerts.md)

---

## 4. Incident Response (Group)
- SCENARIO_NAME: rag_slow
- SYMPTOMS_OBSERVED: Latency P95 tăng vọt từ ~164ms lên > 3600ms, vi phạm SLO nghiêm trọng.
- ROOT_CAUSE_PROVED_BY: Langfuse trace waterfall cho thấy sự gia tăng đột biến trong thời gian xử lý của span 'retrieve'.
- FIX_ACTION: Thực hiện POST /incidents/rag_slow/disable để vô hiệu hóa script tiêm trễ, đưa hệ thống về trạng thái bình thường.
- PREVENTIVE_MEASURE: Thiết lập alert rule 'high_latency_p95' trong Prometheus/Langfuse để cảnh báo khi P95 vượt quá 2000ms.

---

## 5. Individual Contributions & Evidence

### Nguyễn Quang Tùng
- [TASKS_COMPLETED]: Implement toàn bộ `CorrelationIdMiddleware` trong `app/middleware.py`: clear contextvars mỗi request (chống leakage giữa các coroutine), sinh `req-<8hex>` hoặc echo `x-request-id` từ client header, bind `correlation_id` vào structlog contextvars, gắn `x-request-id` và `x-response-time-ms` vào response headers. Viết 3 test cases trong `tests/test_middleware.py` (sinh ID tự động, echo header từ client, response-time header). Fix load `.env` cho `app/main.py`. Cải thiện dashboard HTML UI và thu thập screenshots evidence (estimate100, injected, normal, start).
- [EVIDENCE_LINK]: https://github.com/DangMinh21/Lab13-Observability/pull/1 | https://github.com/DangMinh21/Lab13-Observability/pull/8

### Nguyễn Thị Quỳnh Trang
- [TASKS_COMPLETED]: Mở rộng `app/pii.py` thêm 3 PII patterns mới: `passport_vn` (regex `[A-Z]\d{7,8}`), `address_vn` (số nhà/đường/phường/quận/tỉnh), `bank_account_vn` (số tài khoản 9-14 chữ số); tối ưu compile regex thành compiled patterns. Bật `scrub_event` processor trong pipeline `app/logging_config.py` (đặt trước `JsonlFileProcessor` để PII bị redact trước khi ghi file) và thêm `JsonlFileProcessor` ghi log ra `data/logs.jsonl`. Implement `bind_contextvars` trong `app/main.py` để inject `user_id_hash`, `session_id`, `feature`, `model`, `env` vào mọi log của cùng request. Fix lỗi structlog processor typing.
- [EVIDENCE_LINK]: https://github.com/DangMinh21/Lab13-Observability/pull/2 | https://github.com/DangMinh21/Lab13-Observability/pull/6

### Đặng Văn Minh
- [TASKS_COMPLETED]: Migrate Langfuse từ v2 → v3 API trong `app/tracing.py` (compatibility shim cho `observe`/`langfuse_context`, graceful fallback no-op khi thiếu keys). Thêm `get_audit_logger()` trong `app/logging_config.py` ghi riêng `data/audit.jsonl` cho compliance (field: ts, level, event, user_id_hash, session_id, outcome, latency_ms, cost_usd, quality_score). Tighten SLO targets trong `config/slo.yaml` và thêm alert rule `quality_score_degradation` (P2, trigger < 0.60 for 10m) vào `config/alert_rules.yaml`. Viết runbook đầy đủ cho 4 alerts trong `docs/alerts.md`. Cải thiện `app/mock_llm.py` tạo context-aware answers. Narrow `bank_account_vn` regex tránh false positive. Verify Langfuse traces và thu thập screenshots.
- [EVIDENCE_LINK]: https://github.com/DangMinh21/Lab13-Observability/pull/3 | https://github.com/DangMinh21/Lab13-Observability/pull/7

### Đồng Văn Thịnh
- [TASKS_COMPLETED]: Xây dựng terminal dashboard 6 panels kết nối với endpoint /metrics. Điều phối file blueprint-template.md và quản lý evidence. Thiết lập thư mục docs/screenshots và checklist pass demo. Tối ưu UI Dashboard với single-column layout cho khả năng quan sát tốt hơn.
- [EVIDENCE_LINK]: https://github.com/DangMinh21/Lab13-Observability/pull/4

---

## 6. Bonus Items (Optional)

- [BONUS_COST_OPTIMIZATION]: (+3đ) `app/mock_llm.py` dùng `summarize_text()` để rút gọn prompt trước khi đếm token, giảm `tokens_in`. So sánh: chế độ bình thường ~150 tokens/request; khi bật `cost_spike` incident token count ×4 (~600 tokens/request) — hệ thống detect ngay cost anomaly qua `/metrics` field `avg_cost_usd`. Evidence: `docs/screenshots/estimate100.png` (dashboard trước cost spike), `docs/screenshots/Dashboard_Slow_Rag.png` (sau incident).

- [BONUS_DASHBOARD]: (+3đ) Live HTML dashboard tại `/dashboard` (Chart.js, poll `/metrics` mỗi 1 giây) với 6 panels đầy đủ đơn vị và SLO threshold line: (1) Latency p50/p95/p99 ms, (2) Throughput req/s, (3) Error Rate %, (4) Quality Score avg 0–1, (5) Cost USD avg/total, (6) Token Usage in/out. Dashboard tự cập nhật không cần reload. Evidence: `docs/screenshots/01_dashboard_normal.png`, `docs/screenshots/02_dashboard_breach.png`, `docs/screenshots/03_dashboard_recovered.png`, `docs/screenshots/before_and_after_ragSlow.png`.

- [BONUS_AUDIT_LOG]: (+2đ) Audit log tách riêng ghi vào `data/audit.jsonl` (không lẫn với app log `data/logs.jsonl`) bởi `get_audit_logger()` trong `app/logging_config.py`. Mỗi entry chứa: `ts`, `level`, `event`, `user_id_hash`, `session_id`, `feature`, `correlation_id`, `outcome`, `latency_ms`, `cost_usd`, `quality_score`. Caller tự hash PII trước khi ghi — phù hợp compliance. Evidence: `data/audit.jsonl` (254 entries, committed tại `abdda78`).

- [BONUS_CUSTOM_METRIC]: (+2đ) Heuristic Quality Score (0.0–1.0) tính real-time trong `app/agent.py` dựa trên: độ dài answer (>50 chars), có trả về document context (doc_count > 0), không chứa error keywords. Score này được track trong metrics window 30 giây, exposed qua `/metrics` field `quality_avg`, hiển thị trên dashboard panel 4 với SLO line ≥ 0.70, và trigger alert `quality_score_degradation` khi avg < 0.60 trong 10 phút liên tục.
