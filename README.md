# Day 13 — Lab Quan Sát Hệ Thống (Observability)

Một AI agent FastAPI được trang bị đầy đủ công cụ quan sát ở cấp độ production: structured logging, truyền correlation ID, ẩn PII, distributed tracing (Langfuse), metrics real-time, SLO và alert rules.

---

## Thành viên nhóm

| # | Họ và tên | MSSV | Vai trò | Nhánh |
|---|---|---|---|---|
| 1 | Nguyễn Quang Tùng | 2A202600197 | Correlation ID Middleware + Load Test | `feature/correlation-middleware` |
| 2 | Nguyễn Thị Quỳnh Trang | 2A202600406 | Logging Enrichment + PII Scrubbing | `feature/tv2/logging-pii` |
| 3 | Đặng Văn Minh | 2A202600027 | Tracing (Langfuse) + SLO + Alerts | `feature/tv3/tracing-slo-alerts` |
| 4 | Đồng Văn Thịnh | 2A202600365 | Dashboard + Tài liệu + Điều phối Demo | `feature/tv4/dashboard-docs` |

---

## Những gì dự án này thể hiện

| Lớp | Cài đặt |
|---|---|
| **Structured Logging** | `structlog` ghi JSON lines ra `data/logs.jsonl`; mỗi log tự động mang `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model` |
| **Correlation ID** | `CorrelationIdMiddleware` sinh `req-<8hex>` mỗi request (hoặc echo lại `x-request-id` từ client), truyền vào tất cả log và response headers |
| **PII Scrubbing** | Scrubber dùng regex loại bỏ email, số điện thoại VN, CCCD, thẻ tín dụng, hộ chiếu, địa chỉ và số tài khoản ngân hàng trước khi ghi log |
| **Audit Logging** | `data/audit.jsonl` riêng biệt lưu ai-làm-gì cho mục đích compliance; caller tự hash PII trước khi ghi |
| **Distributed Tracing** | Decorator `@observe()` của Langfuse v3 bọc toàn bộ pipeline agent; trace có user hash, session, tags và thông tin token |
| **Metrics** | Metrics in-memory theo cửa sổ thời gian (30 giây): p50/p95/p99 latency, cost trung bình/tổng, số token, quality score, phân tích lỗi |
| **Dashboard** | Live dashboard HTML tại `/dashboard` poll `/metrics` mỗi 1 giây, hiển thị 6 panels |
| **SLO** | Định nghĩa trong `config/slo.yaml`: latency p95 < 2s, error rate < 1%, daily cost < $2, quality avg ≥ 0.70 |
| **Alert Rules** | Định nghĩa trong `config/alert_rules.yaml`: 4 rules (P1/P2) kèm link runbook |
| **Incident Injection** | Ba chế độ lỗi có thể bật/tắt để stress-test hệ thống quan sát theo thời gian thực |

---

## Kiến trúc hệ thống

```
POST /chat
     │
     ▼
CorrelationIdMiddleware        — sinh x-request-id, bind vào structlog context
     │
     ▼
chat() endpoint (main.py)      — bind user/session/feature vào context, gọi agent
     │
     ▼
LabAgent.run()  @observe()     — Langfuse trace bọc toàn bộ pipeline
  ├── mock_rag.retrieve()      — tìm kiếm từ khoá trong CORPUS (inject: rag_slow, tool_fail)
  ├── FakeLLM.generate()       — câu trả lời xác định (inject: cost_spike)
  ├── metrics.record_request() — cập nhật stats in-memory theo cửa sổ thời gian
  └── langfuse_context.update_current_trace()
     │
     ▼
Structured log → data/logs.jsonl   (PII đã scrub)
Audit log      → data/audit.jsonl  (ID đã hash)
Response       → ChatResponse (gồm correlation_id, latency_ms, cost_usd, quality_score)
```

---

## Cấu trúc thư mục

```
Lab13-Observability/
│
├── app/                            # Source code ứng dụng FastAPI
│   ├── main.py                     # Điểm vào app: endpoints /chat /health /metrics /dashboard
│   │                               #   → bind_contextvars cho user/session/feature/model
│   │                               #   → audit log mỗi request
│   ├── agent.py                    # Pipeline AI: RAG → LLM → metrics → Langfuse trace
│   │                               #   → @observe() tự động tạo trace Langfuse
│   │                               #   → tính quality_score heuristic + ước tính cost
│   ├── middleware.py               # CorrelationIdMiddleware
│   │                               #   → sinh req-<8hex> hoặc echo x-request-id từ header
│   │                               #   → clear_contextvars() mỗi request (chống leakage)
│   │                               #   → gắn x-request-id + x-response-time-ms vào response
│   ├── logging_config.py           # Cấu hình structlog
│   │                               #   → pipeline: merge_contextvars → add_log_level → timestamp
│   │                               #              → scrub_event (PII) → JsonlFileProcessor → JSON
│   │                               #   → get_audit_logger(): logger riêng ghi data/audit.jsonl
│   ├── pii.py                      # PII scrubber
│   │                               #   → 8 regex patterns: email, phone_vn, cccd, credit_card,
│   │                               #     passport_vn, address_vn, bank_account_vn
│   │                               #   → scrub_text(), summarize_text(), hash_user_id()
│   ├── tracing.py                  # Langfuse v3 integration
│   │                               #   → observe, langfuse_context (wrapper tương thích v2→v3)
│   │                               #   → fallback no-op nếu không có API keys
│   ├── metrics.py                  # In-memory metrics (cửa sổ 30 giây)
│   │                               #   → record_request(), record_error(), snapshot()
│   │                               #   → percentile() tính p50/p95/p99
│   ├── incidents.py                # Toggle các failure scenarios
│   │                               #   → STATE: {rag_slow, tool_fail, cost_spike}
│   │                               #   → enable() / disable() / status()
│   ├── mock_llm.py                 # Fake LLM (không dùng API thật)
│   │                               #   → sleep 0.15s, đếm token từ độ dài prompt
│   │                               #   → cost_spike → tokens × 4
│   ├── mock_rag.py                 # Fake RAG retrieval (3 chủ đề: refund/monitoring/policy)
│   │                               #   → rag_slow → sleep 2.5s
│   │                               #   → tool_fail → raise RuntimeError
│   ├── schemas.py                  # Pydantic models: ChatRequest, ChatResponse, LogRecord
│   └── dashboard.html              # Live dashboard HTML (6 panels, Chart.js, poll /metrics 1s)
│
├── config/                         # Cấu hình observability
│   ├── slo.yaml                    # 4 SLI: latency p95 < 2s, error < 1%, cost < $2, quality ≥ 0.70
│   ├── alert_rules.yaml            # 4 alert rules (P1/P2) kèm link runbook
│   └── logging_schema.json         # Schema kiểm tra log (dùng bởi validate_logs.py)
│
├── scripts/                        # Công cụ chạy tay
│   ├── load_test.py                # Sinh requests đồng thời (--concurrency N)
│   ├── inject_incident.py          # Bật/tắt incident scenarios qua HTTP API
│   └── validate_logs.py            # Kiểm tra schema + PII compliance của data/logs.jsonl
│
├── data/                           # Output runtime (tự động tạo khi chạy app)
│   ├── logs.jsonl                  # Structured app logs (PII đã scrub)
│   ├── audit.jsonl                 # Audit trail compliance (user_id đã hash)
│   ├── sample_queries.jsonl        # Bộ câu hỏi test cho load_test.py
│   └── incidents.json              # Mô tả các failure scenarios
│
├── docs/                           # Tài liệu + bằng chứng
│   ├── blueprint-template.md       # Báo cáo nhóm + đóng góp cá nhân
│   ├── alerts.md                   # Runbook xử lý từng alert
│   ├── dashboard-spec.md           # Checklist 6 panels dashboard
│   ├── grading-evidence.md         # Danh sách bằng chứng cho chấm điểm
│   └── screenshots/                # Screenshots bằng chứng (xem mục Chấm điểm bên dưới)
│       ├── langfuse_trace_list.png         # ≥ 10 traces trên Langfuse
│       ├── Specific_trace_in_langfuse.png  # Chi tiết 1 trace
│       ├── Validate_logs.png               # Output validate_logs.py
│       ├── Dashboard_normal_1.png          # Dashboard trạng thái bình thường
│       ├── Dashboard_Slow_Rag.png          # Dashboard khi rag_slow bật
│       ├── before_and_after_ragSlow.png    # So sánh trước/sau incident
│       └── PII_Injection.png               # Minh chứng PII bị scrub
│
├── plans/                          # Kế hoạch cá nhân từng thành viên
│   ├── Nguyen_Quang_Tung-2A202600197.md
│   ├── Nguyen_Thi_Quynh_Trang_2A202600406.md
│   ├── Dang_Van_Minh_2A202600027.md
│   └── Dong_Van_Thinh_2A202600365.md
│
├── tests/                          # Unit tests
│   ├── test_middleware.py           # Test CorrelationIdMiddleware (3 trường hợp)
│   ├── test_metrics.py              # Test tính percentile
│   └── test_pii.py                  # Test hàm scrub_text
│
├── requirements.txt                # fastapi, uvicorn, structlog, langfuse, pytest, httpx, pydantic
├── .env.example                    # Template biến môi trường (copy → .env)
└── .gitignore
```

---

## Cài đặt nhanh

### Bước 1 — Cài thư viện

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Bước 2 — Cấu hình

```bash
cp .env.example .env
```

Mở `.env` và điền Langfuse keys (tuỳ chọn — app vẫn chạy ở chế độ no-op nếu không có):

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Bước 3 — Khởi động

```bash
uvicorn app.main:app --reload
```

App chạy tại `http://127.0.0.1:8000`.

| Endpoint | Mô tả |
|---|---|
| `GET /health` | Trạng thái hệ thống + incidents đang active |
| `GET /metrics` | Snapshot metrics real-time |
| `GET /dashboard` | HTML dashboard (6 panels) |
| `POST /chat` | Endpoint AI agent chính |
| `POST /incidents/{name}/enable` | Bật failure scenario |
| `POST /incidents/{name}/disable` | Tắt failure scenario |

---

## Phân công công việc

### Nguyễn Quang Tùng — 2A202600197

**Vai trò:** Correlation ID Middleware + Load Test / Incident Injection

**File chịu trách nhiệm:**
- `app/middleware.py` — cài đặt toàn bộ `CorrelationIdMiddleware`
- `tests/test_middleware.py` — 3 test cases: tự sinh ID, echo header, response-time header

**Commits chính:**

| Commit | Nội dung |
|---|---|
| `e26aff3` | `feat(middleware): implement correlation ID generation and propagation` |
| `b5a69fd` | `feat(middleware): implement CorrelationIdMiddleware` (kèm test) |
| `e4e8e8b` | `fix: load environment variables from .env file` |

**Kiểm tra:**
```bash
# Middleware sinh đúng format
curl -si http://127.0.0.1:8000/health | grep x-request-id
# Mong đợi: x-request-id: req-xxxxxxxx

# Echo header từ client
curl -si http://127.0.0.1:8000/health -H "x-request-id: my-custom-id" | grep x-request-id
# Mong đợi: x-request-id: my-custom-id

# Chạy tests
pytest tests/test_middleware.py -v
```

---

### Nguyễn Thị Quỳnh Trang — 2A202600406

**Vai trò:** Logging Enrichment + PII Scrubbing

**File chịu trách nhiệm:**
- `app/pii.py` — mở rộng PII patterns (passport, address_vn, bank_account_vn), tối ưu compile regex
- `app/logging_config.py` — bật `scrub_event` processor trong pipeline, thêm `JsonlFileProcessor`
- `app/main.py` — cài đặt `bind_contextvars` để inject context vào mọi log

**Commits chính:**

| Commit | Nội dung |
|---|---|
| `142a046` | `feat(observability): enrich log context, harden PII scrubbing, and fix structlog processor typing` |

**Kiểm tra:**
```bash
# Gửi request có PII
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","session_id":"s1","feature":"qa","message":"email abc@test.com sdt 0912345678"}'

# Log phải có correlation_id, user_id_hash, session_id, feature, model
# KHÔNG được có email/phone thật
tail -1 data/logs.jsonl | python -m json.tool

# Chạy validation đầy đủ
python scripts/validate_logs.py

# Unit test PII
pytest tests/test_pii.py -v
```

---

### Đặng Văn Minh — 2A202600027

**Vai trò:** Tracing (Langfuse) + SLO + Alerts + Audit Log

**File chịu trách nhiệm:**
- `app/tracing.py` — chuyển từ Langfuse v2 → v3 API, cài đặt compatibility shim, graceful fallback
- `app/logging_config.py` — thêm `get_audit_logger()` ghi `data/audit.jsonl`
- `app/mock_llm.py` — cải thiện `_build_answer()` tạo câu trả lời context-aware
- `config/slo.yaml` — tighten SLO targets, thêm ghi chú đo lường
- `config/alert_rules.yaml` — thêm alert `quality_score_degradation`
- `docs/alerts.md` — viết runbook cho 4 alerts

**Commits chính:**

| Commit | Nội dung |
|---|---|
| `c70f54f` | `fix(tracing): migrate Langfuse decorators to v3 API and load .env` |
| `b6a481b` | `feat(slo): tighten SLO targets and add quality degradation alert with runbook` |
| `0b6fdf6` | `feat(audit): add separate audit log to data/audit.jsonl for compliance` |
| `a5bc9e9` | `fix(pii): narrow bank_account_vn regex; feat(mock-llm): context-aware answers` |

**Kiểm tra:**
```bash
# Tracing có hoạt động không
curl http://127.0.0.1:8000/health | python -m json.tool
# Field "tracing_enabled": true (nếu có Langfuse keys)

# Audit log
tail -3 data/audit.jsonl | python -m json.tool
# Phải có: ts, level, event, user_id_hash, session_id, outcome, latency_ms

# Xem cấu hình SLO và alert
cat config/slo.yaml
cat config/alert_rules.yaml

# Langfuse: vào https://cloud.langfuse.com → Traces → đếm ≥ 10 traces
```

---

### Đồng Văn Thịnh — 2A202600365

**Vai trò:** Dashboard + Tài liệu + Điều phối Demo

**File chịu trách nhiệm:**
- `app/dashboard.html` — xây dựng toàn bộ live dashboard HTML (6 panels, Chart.js, poll /metrics)
- `app/main.py` — thêm endpoint `/dashboard`, cải thiện startup/shutdown handlers
- `docs/blueprint-template.md` — viết và điều phối báo cáo nhóm
- `docs/screenshots/` — thu thập và tổ chức bằng chứng cho chấm điểm
- `plans/` — tạo kế hoạch cá nhân cho từng thành viên

**Commits chính:**

| Commit | Nội dung |
|---|---|
| `fe6ba63` | `feat: add observability dashboard UI, main application logic, and lab report template` |
| `ca50a9d` | `feat: create member plan for Langfuse tracing, SLO configuration, and alert rules` |
| `8b332bd` | `docs: add lab report template and organize dashboard evidence screenshots` |
| `716880c` | `Move screenshot to docs/screenshot` |

**Kiểm tra:**
```bash
# Mở dashboard
open http://127.0.0.1:8000/dashboard

# Chạy load test → xem dashboard cập nhật real-time
python scripts/load_test.py --concurrency 3

# Xem screenshots bằng chứng
ls docs/screenshots/
```

---

## Hướng dẫn chấm điểm

### Bước 1 — Cài đặt môi trường (2 phút)

```bash
git clone <repo-url> && cd Lab13-Observability
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # điền Langfuse keys nếu muốn verify traces
uvicorn app.main:app --reload
```

### Bước 2 — Chạy validation tự động

```bash
# Xoá log cũ để test sạch
rm -f data/logs.jsonl data/audit.jsonl

# Sinh 15-20 requests
python scripts/load_test.py --concurrency 5

# Kiểm tra schema — output cho biết % log đạt chuẩn
python scripts/validate_logs.py

# Chạy unit tests
pytest tests/ -v
```

### Bước 3 — Checklist kỹ thuật

| Hạng mục | Cách kiểm tra | File liên quan |
|---|---|---|
| **Correlation ID đúng format** | `curl -si /health \| grep x-request-id` → phải là `req-xxxxxxxx` | `app/middleware.py` |
| **Echo correlation ID từ header** | Gửi `x-request-id: abc` → response trả về đúng `abc` | `app/middleware.py` |
| **Log có đủ required fields** | `validate_logs.py` → `ts, level, service, event, correlation_id` | `app/logging_config.py` |
| **Log có enrichment fields** | `validate_logs.py` → `user_id_hash, session_id, feature, model` | `app/main.py` |
| **PII không xuất hiện trong log** | `grep "gmail.com" data/logs.jsonl` → không có kết quả | `app/pii.py` |
| **PII bị thay đúng tag** | `tail -1 data/logs.jsonl` → thấy `[REDACTED_EMAIL]` | `app/pii.py` |
| **Audit log ghi riêng** | `cat data/audit.jsonl` → có `event, user_id_hash, outcome` | `app/logging_config.py` |
| **Langfuse traces ≥ 10** | Vào Langfuse dashboard → Traces → đếm | `app/tracing.py` + `app/agent.py` |
| **Trace có tags đúng** | Click vào 1 trace → xem tags: `["lab", "qa", "claude-sonnet-4-5"]` | `app/agent.py` |
| **SLO đủ 4 SLI** | `cat config/slo.yaml` | `config/slo.yaml` |
| **Alert rules đủ 4 rules** | `cat config/alert_rules.yaml` | `config/alert_rules.yaml` |
| **Dashboard hiển thị 6 panels** | Mở `/dashboard` → đếm: Latency, Throughput, Reliability, Quality, Cost, Tokens | `app/dashboard.html` |
| **Metrics phản ứng với incident** | Bật `rag_slow` → chạy load test → latency p95 tăng | `app/incidents.py` |

### Bước 4 — Kiểm tra incident injection

```bash
# Test rag_slow: latency tăng
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 3
curl http://127.0.0.1:8000/metrics | python -m json.tool   # latency_p95 > 2000ms
python scripts/inject_incident.py --scenario rag_slow --disable

# Test tool_fail: error rate tăng
python scripts/inject_incident.py --scenario tool_fail
python scripts/load_test.py --concurrency 3   # terminal hiện [500]
curl http://127.0.0.1:8000/metrics | python -m json.tool   # error_breakdown có RuntimeError
python scripts/inject_incident.py --scenario tool_fail --disable
```

### Bước 5 — Xem screenshots bằng chứng

Tất cả screenshots nằm trong `docs/screenshots/`:

| File | Nội dung |
|---|---|
| `langfuse_trace_list.png` | Danh sách ≥ 10 traces trên Langfuse |
| `Specific_trace_in_langfuse.png` | Chi tiết 1 trace (span, token usage, tags) |
| `Validate_logs.png` | Output `validate_logs.py` pass |
| `Dashboard_normal_1.png` | Dashboard trạng thái bình thường |
| `Dashboard_Slow_Rag.png` | Dashboard khi `rag_slow` active (latency spike) |
| `before_and_after_ragSlow.png` | So sánh metrics trước/sau incident |
| `PII_Injection.png` | Log hiển thị `[REDACTED_*]` thay vì PII thật |

---

## Kịch bản demo

Demo chia **4 hồi** (~15 phút). Chuẩn bị trước khi bắt đầu:
- **Terminal 1** — app server đang chạy
- **Terminal 2** — để chạy load test / inject incident
- **Tab trình duyệt 1** — `http://127.0.0.1:8000/dashboard`
- **Tab trình duyệt 2** — Langfuse dashboard (nếu có keys)

### Hồi 1 — Hoạt động bình thường (3 phút)

**Mục tiêu:** Chứng minh hệ thống healthy, 3 lớp quan sát đều hoạt động.

```bash
# Bước 1: Kiểm tra health
curl http://127.0.0.1:8000/health
# Mong đợi: {"ok": true, "incidents": {"rag_slow": false, "tool_fail": false, "cost_spike": false}}

# Bước 2: Sinh requests
python scripts/load_test.py --concurrency 3
# Output: [200] req-a1b2c3d4 | qa | 165ms

# Bước 3: Kiểm tra log — phải có correlation_id, user_id_hash, session_id
tail -1 data/logs.jsonl | python -m json.tool

# Bước 4: Validate schema
python scripts/validate_logs.py
```

Chỉ cho người xem thấy dashboard cập nhật real-time và traces trên Langfuse.

### Hồi 2 — PII scrubbing (2 phút)

**Mục tiêu:** Chứng minh PII không bao giờ ghi vào log.

```bash
# Gửi request có PII
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u_demo","session_id":"s1","feature":"qa","message":"email demo@test.com sdt 0912345678 refund"}'

# Kiểm tra log
tail -1 data/logs.jsonl | python -m json.tool
# Thấy: "message_preview": "email [REDACTED_EMAIL] sdt [REDACTED_PHONE_VN] refund"
```

### Hồi 3 — Incident: RAG chậm (5 phút)

**Mục tiêu:** Simulate incident thật, xem metrics xuống cấp real-time.

```bash
# Bật incident
python scripts/inject_incident.py --scenario rag_slow

# Chạy load test — xem dashboard latency p95 tăng từ ~160ms → ~2600ms
python scripts/load_test.py --concurrency 5

# Xem log latency cao
tail -3 data/logs.jsonl | python -m json.tool   # latency_ms ~2600

# Khôi phục → dashboard recover trong vài giây
python scripts/inject_incident.py --scenario rag_slow --disable
```

Chỉ ra: alert `high_latency_p95` trong `config/alert_rules.yaml` sẽ trigger khi p95 > 5000ms trong 30 phút.

### Hồi 4 — Incident: Tỉ lệ lỗi tăng đột biến (3 phút)

**Mục tiêu:** Chứng minh error path được log và alert đúng.

```bash
# Bật incident
python scripts/inject_incident.py --scenario tool_fail

# Load test → tất cả [500]
python scripts/load_test.py --concurrency 3

# Xem error log
grep '"level":"error"' data/logs.jsonl | tail -1 | python -m json.tool
# Có: error_type, correlation_id, message_preview (PII đã scrub)

# Khôi phục
python scripts/inject_incident.py --scenario tool_fail --disable
```

### Kết thúc (2 phút)

```bash
python scripts/validate_logs.py
curl -s http://127.0.0.1:8000/metrics | python -m json.tool
pytest tests/ -v
```

---

## Tham chiếu công cụ

```bash
# Load test (mặc định concurrency=1)
python scripts/load_test.py --concurrency 5

# Bật / tắt incidents
python scripts/inject_incident.py --scenario rag_slow
python scripts/inject_incident.py --scenario rag_slow --disable
python scripts/inject_incident.py --scenario tool_fail
python scripts/inject_incident.py --scenario tool_fail --disable
python scripts/inject_incident.py --scenario cost_spike
python scripts/inject_incident.py --scenario cost_spike --disable

# Kiểm tra log schema và PII
python scripts/validate_logs.py

# Unit tests
pytest tests/ -v
```

Các incident scenarios:

| Scenario | Hiệu ứng | Metric bị ảnh hưởng |
|---|---|---|
| `rag_slow` | RAG sleep 2.5 giây/lần gọi | latency p95/p99 tăng đột biến |
| `tool_fail` | RAG raise RuntimeError | error rate tăng, HTTP 500 |
| `cost_spike` | Token count × 4 | cost/request × 4 |

---

## Chính sách chấm điểm (60/40)

1. **Điểm nhóm (60%)**
   - Cài đặt kỹ thuật (30 điểm) — xác minh bằng `validate_logs.py` và hệ thống trực tiếp
   - Phân tích sự cố (10 điểm) — root cause analysis trong `docs/blueprint-template.md`
   - Live demo (20 điểm) — thuyết trình theo kịch bản 4 hồi

2. **Điểm cá nhân (40%)**
   - Báo cáo cá nhân (20 điểm) — đóng góp ghi trong `docs/blueprint-template.md`
   - Bằng chứng Git (20 điểm) — commits có tên tác giả, message rõ ràng, PR có thể truy xuất

**Tiêu chí đạt:**
- `validate_logs.py` pass (không thiếu required field, không có PII trong log)
- Ít nhất 10 traces hiển thị trên Langfuse
- Dashboard hiển thị đủ 6 panels
- Tất cả TODO blocks đã hoàn thành
