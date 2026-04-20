# Kế hoạch cá nhân — Thành-viên-#2

**Role**: Logging & PII  
**Branch**: `feature/tv2/logging-pii`

---

## Tại sao role này quan trọng

PII leak trong `validate_logs.py` trừ **30 điểm**. Log enrichment (thiếu `user_id_hash`, `session_id`, `feature`, `model`) trừ thêm 20 điểm. Đây là 50/100 điểm kỹ thuật — cao nhất trong nhóm.

Phụ thuộc Thành-viên-#1 xong middleware trước T+1:00 để test đầy đủ.

---

## Timeline cá nhân

| Thời gian | Việc làm |
|---|---|
| T+0:00 → T+0:15 | Setup: clone, virtualenv, pip install, tạo branch |
| T+0:15 → T+0:30 | Implement `app/pii.py` — thêm PII patterns |
| T+0:30 → T+0:50 | Implement `app/logging_config.py` — bật scrub_event |
| T+0:50 → T+1:10 | Implement `app/main.py` — bind_contextvars |
| T+1:10 → T+1:30 | Test với Thành-viên-#1, commit, chuẩn bị PR |
| T+1:40 → T+1:50 | Mở PR → review → merge |
| T+2:30 → T+2:50 | Thu thập screenshot, điền blueprint |

---

## Nhiệm vụ kỹ thuật chi tiết

### 1. Mở rộng `app/pii.py` — thêm PII patterns

File hiện có: email, phone_vn, cccd, credit_card. Cần thêm:

```python
PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone_vn": r"(?:\+84|0)[ \.-]?\d{3}[ \.-]?\d{3}[ \.-]?\d{3,4}",
    "cccd": r"\b\d{12}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    # TODO: thêm patterns mới
    "passport_vn": r"\b[A-Z]\d{7,8}\b",          # VD: B1234567
    "address_vn": r"(?i)(số\s+\d+|đường\s+\w+|phường\s+\w+|quận\s+\w+|tỉnh\s+\w+)",
    "bank_account_vn": r"\b\d{9,14}\b",           # Tài khoản ngân hàng VN 9-14 số
}
```

**Test:**
```python
from app.pii import scrub_text
assert "[REDACTED_EMAIL]" in scrub_text("user@gmail.com")
assert "[REDACTED_PHONE_VN]" in scrub_text("0901234567")
assert "[REDACTED_PASSPORT_VN]" in scrub_text("B1234567")
print("PII tests passed")
```

### 2. Bật PII scrubber trong `app/logging_config.py`

Uncomment dòng `scrub_event` trong processor chain:

```python
def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            scrub_event,          # <-- uncomment dòng này
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JsonlFileProcessor(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
```

**Lưu ý quan trọng**: `scrub_event` phải đặt TRƯỚC `JsonlFileProcessor` để file log không bao giờ chứa PII thô.

### 3. Implement log enrichment trong `app/main.py`

Uncomment và điền đầy đủ `bind_contextvars` trong hàm `chat`:

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    # Bind context vào tất cả log trong request này
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        model=agent.model,
        env=os.getenv("APP_ENV", "dev"),
    )
    # ... phần còn lại giữ nguyên
```

**Điểm kiểm tra:**
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test@example.com","session_id":"sess-001","feature":"search","message":"hello"}' \
  > /dev/null

# Xem log dòng cuối
tail -1 data/logs.jsonl | python -m json.tool
# Phải thấy: user_id_hash, session_id, feature, model, correlation_id
# KHÔNG được thấy: email nguyên bản
```

---

## Test tổng hợp với validate_logs.py

```bash
# Xóa log cũ để test sạch
rm -f data/logs.jsonl

# Gửi vài request với PII test
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","session_id":"s1","feature":"chat","message":"email là abc@test.com"}'

curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u2","session_id":"s2","feature":"search","message":"số thẻ 4111111111111111"}'

# Chạy validate
python scripts/validate_logs.py
# Mục tiêu: PASSED tất cả 4 checks, score = 100
```

---

## Git workflow

```bash
# Setup branch
git checkout -b feature/tv2/logging-pii

# Commit từng phần riêng (quan trọng cho Git Evidence score)
git add app/pii.py
git commit -m "feat(pii): add passport, address, bank account patterns"

git add app/logging_config.py
git commit -m "feat(logging): enable PII scrub_event processor"

git add app/main.py
git commit -m "feat(api): bind user context to structlog contextvars"

# Push và mở PR
git push -u origin feature/tv2/logging-pii
# PR title: "feat: implement logging enrichment and PII scrubbing"
# Request Thành-viên-#1 review
```

---

## Evidence cần thu thập

- [ ] Screenshot log line có `user_id_hash`, `session_id`, `feature`, `correlation_id`
- [ ] Screenshot log line với `[REDACTED_EMAIL]` hoặc `[REDACTED_PHONE_VN]`
- [ ] Output `validate_logs.py` đạt ≥ 80 — chụp toàn màn hình terminal
- [ ] Link 3 commits riêng biệt trên GitHub

---

## Phần điền trong `docs/blueprint-template.md`

```
### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: Mở rộng PII patterns (passport, địa chỉ, tài khoản ngân hàng). Bật scrub_event processor trong logging pipeline. Implement bind_contextvars cho user/session/feature/model context.
- [EVIDENCE_LINK]: <link PR>
```

---

## Câu hỏi giảng viên có thể hỏi

1. Tại sao đặt `scrub_event` trước `JsonlFileProcessor`?  
   → Để PII bị redact trước khi ghi vào file. Nếu đặt sau, file log sẽ chứa dữ liệu thô.

2. Tại sao dùng `hash_user_id` thay vì log raw `user_id`?  
   → SHA-256 12 ký tự đầu đủ để correlate các request của cùng user mà không expose PII. Không thể reverse-engineer được email gốc.

3. `bind_contextvars` hoạt động thế nào?  
   → Gắn key-value vào context variable của coroutine hiện tại. `merge_contextvars` processor trong structlog tự động inject chúng vào mọi log event trong cùng request — không cần truyền tay.
