# Kế hoạch cá nhân — Thành-viên-#1

**Role**: Correlation ID Middleware & Incident Debug  
**Branch**: `feature/tv1/correlation-middleware`

---

## Tại sao role này quan trọng

Middleware là **dependency** của toàn team: nếu `correlation_id = "MISSING"`, `validate_logs.py` sẽ trừ 20 điểm và Thành-viên-#2 không thể test log enrichment đúng cách. Cần xong trước T+1:00.

---

## Timeline cá nhân

| Thời gian | Việc làm |
|---|---|
| T+0:00 → T+0:15 | Setup: clone, virtualenv, pip install, tạo branch |
| T+0:15 → T+0:45 | Implement `app/middleware.py` (4 TODOs) |
| T+0:45 → T+1:00 | Test middleware locally, commit, thông báo Thành-viên-#2 |
| T+1:00 → T+1:30 | Test tích hợp với Thành-viên-#2, chuẩn bị PR |
| T+1:30 → T+1:40 | Mở PR → được review → merge vào main |
| T+2:00 → T+2:20 | Chạy load test sinh data |
| T+2:15 → T+2:25 | Inject incident + phân tích root cause |
| T+2:30 → T+2:50 | Cung cấp screenshot, điền phần mình trong blueprint |

---

## Nhiệm vụ kỹ thuật chi tiết

### 1. Implement `app/middleware.py`

File hiện tại có 4 TODO cần implement:

```python
from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # TODO 1: Clear contextvars để tránh leakage giữa các request
        clear_contextvars()

        # TODO 2: Lấy x-request-id từ header hoặc tự sinh mới
        # Format: req-<8-char-hex>
        correlation_id = (
            request.headers.get("x-request-id")
            or f"req-{uuid.uuid4().hex[:8]}"
        )

        # TODO 3: Bind correlation_id vào structlog contextvars
        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        # TODO 4: Gắn headers vào response
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(elapsed_ms)

        return response
```

**Điểm kiểm tra sau khi implement:**
```bash
uvicorn app.main:app --reload &
curl -s http://localhost:8000/health | python -m json.tool
curl -si -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","session_id":"s1","feature":"search","message":"hello"}' \
  | grep -E "x-request-id|x-response-time"
# Phải thấy: x-request-id: req-xxxxxxxx
```

### 2. Chạy load test (T+2:00 → T+2:20)

```bash
# Tạo đủ data cho validate_logs và Langfuse
python scripts/load_test.py --concurrency 5
# Chạy ít nhất 2-3 lần để có ≥ 10 requests → ≥ 10 traces
```

### 3. Inject incident + phân tích (T+2:15 → T+2:25)

```bash
# Bật incident
python scripts/inject_incident.py --scenario rag_slow

# Ghi lại latency (so sánh /metrics trước và sau)
curl http://localhost:8000/metrics

# Tắt incident
python scripts/inject_incident.py --scenario rag_slow --disable
```

**Ghi chú cho blueprint report** — điền phần Incident Response:
- `[SCENARIO_NAME]`: `rag_slow`
- `[SYMPTOMS_OBSERVED]`: latency_p95 tăng đột biến (so sánh số liệu trước/sau)
- `[ROOT_CAUSE_PROVED_BY]`: trace ID có span `retrieve` dài bất thường (thấy trên Langfuse)
- `[FIX_ACTION]`: disable incident toggle qua `/incidents/rag_slow/disable`
- `[PREVENTIVE_MEASURE]`: alert `high_latency_p95` trigger khi latency_p95 > 5000ms

---

## Git workflow

```bash
# Setup branch
git checkout -b feature/tv1/correlation-middleware

# Sau khi implement xong
git add app/middleware.py
git commit -m "feat(middleware): implement correlation ID generation and propagation"

# Sau khi test thêm
git add app/middleware.py
git commit -m "fix(middleware): ensure contextvars cleared between requests"

# Push và mở PR
git push -u origin feature/tv1/correlation-middleware
# Mở PR trên GitHub: feature/tv1/correlation-middleware → main
# Title: "feat: add correlation ID middleware"
# Request Thành-viên-#2 review
```

---

## Evidence cần thu thập

- [ ] Screenshot response header có `x-request-id: req-xxxxxxxx`
- [ ] Screenshot log line có `"correlation_id": "req-xxxxxxxx"`
- [ ] Screenshot `/metrics` trước và sau `rag_slow` incident (số liệu latency tăng)
- [ ] Link PR đã được merge

---

## Phần điền trong `docs/blueprint-template.md`

```
### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: Implement CorrelationIdMiddleware (clear_contextvars, generate req-<hex>, bind structlog, response headers). Chạy load test tạo data. Inject và phân tích incident rag_slow.
- [EVIDENCE_LINK]: <link PR>
```

---

## Câu hỏi giảng viên có thể hỏi

1. Tại sao cần `clear_contextvars()` ở đầu mỗi request?  
   → Vì Starlette tái sử dụng thread/coroutine, contextvars từ request trước có thể bị leak sang request sau.

2. Tại sao dùng `uuid4().hex[:8]` thay vì UUID đầy đủ?  
   → Ngắn gọn, dễ đọc trong log, entropy đủ cho mục đích correlation trong single-service.

3. Làm sao biết incident `rag_slow` đang active hay không?  
   → `GET /health` trả về field `incidents` với trạng thái từng toggle.
