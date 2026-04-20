# Lab 13 Observability — Kế hoạch nhóm (3 giờ)

## Thông tin nhóm

| # | Họ tên | MSSV | Role trong lab |
|---|---|---|---|
| 1 | Nguyễn Quang Tùng | 2A202600197 |  |
| 2 | Đặng Văn Minh | 2A202600027 |  |
| 3 | Nguyễn Thị Quỳnh Trang | 2A202600406 |  |
| 4 | Đồng Văn Thịnh | 2A202600365 |  |

---

## Mục tiêu điểm

| Hạng mục | Điểm tối đa | Mục tiêu |
|---|---:|---:|
| Implementation (Logging, Tracing, Alerts, PII) | 30 | 28+ |
| Incident Debug | 10 | 10 |
| Live Demo | 20 | 18+ |
| Individual Report | 20 | 18+ |
| Git Evidence | 20 | 20 |
| **Tổng** | **100** | **94+** |
| Bonus | 10 | +5 |

---

## Git Workflow

```
main (protected)
 ├── feature/tv1/correlation-middleware
 ├── feature/tv2/logging-pii
 ├── feature/tv3/tracing-slo-alerts
 └── feature/tv4/dashboard-docs
```

**Quy tắc:**
- Mỗi thành viên làm việc trên branch riêng
- Commit message format: `type(scope): mô tả ngắn` — vd: `feat(middleware): add correlation id generation`
- Mở PR → request 1 người review → merge vào `main`
- Thứ tự merge: Thành-viên-#1 trước (middleware là dependency) → #2 → #3 → #4

---

## Timeline 3 giờ

```
T+0:00 ─ T+0:15  [PHASE 0] Setup
T+0:15 ─ T+1:30  [PHASE 1] Implement song song (4 người)
T+1:30 ─ T+2:00  [PHASE 2] Tích hợp — merge PRs, validate_logs
T+2:00 ─ T+2:30  [PHASE 3] Dashboard + Load test + Incident injection
T+2:30 ─ T+2:50  [PHASE 4] Thu thập evidence + điền blueprint report
T+2:50 ─ T+3:00  [PHASE 5] Demo prep
```

---

## PHASE 0 — Setup (T+0:00 → T+0:15, tất cả)

**Tất cả thành viên thực hiện:**

```bash
# 1. Clone repo (nếu chưa có)
git clone <REPO_URL>
cd Lab13-Observability

# 2. Tạo virtualenv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Copy env
cp .env.example .env
# Điền LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY (do Thành-viên-#3 cung cấp)

# 4. Tạo branch riêng
git checkout -b feature/tv<số>/<scope>
```

**Thành-viên-#3** cần: Tạo Langfuse project → chia sẻ Public Key + Secret Key vào nhóm chat trước T+0:10.

---

## PHASE 1 — Implementation song song (T+0:15 → T+1:30)

| Thành viên | File chính | Chi tiết |
|---|---|---|
| Thành-viên-#1 | `app/middleware.py` | 4 TODOs: clear contextvars, generate req-\<8hex\>, bind, response headers |
| Thành-viên-#2 | `app/main.py`, `app/logging_config.py`, `app/pii.py` | bind_contextvars + scrub_event + thêm PII patterns |
| Thành-viên-#3 | `.env`, `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md` | Langfuse keys + refine SLOs + alert thứ 4 + runbook |
| Thành-viên-#4 | `docs/blueprint-template.md`, `scripts/dashboard.py` | Điền metadata nhóm + build dashboard script |

**Checkpoint T+1:00**: Thành-viên-#1 phải xong middleware để Thành-viên-#2 test bind_contextvars.

---

## PHASE 2 — Tích hợp (T+1:30 → T+2:00)

```
T+1:30  Thành-viên-#1 mở PR → #2 review → merge
T+1:40  Thành-viên-#2 mở PR → #1 review → merge
T+1:45  Thành-viên-#3 mở PR → review → merge
T+1:50  Thành-viên-#4 mở PR → review → merge

T+1:55  Chạy validate_logs.py lần đầu — ghi lại score
        python scripts/validate_logs.py
T+2:00  Sửa lỗi nếu score < 80
```

---

## PHASE 3 — Dashboard + Data (T+2:00 → T+2:30)

```
T+2:00  Khởi động server: uvicorn app.main:app --reload
T+2:05  Thành-viên-#1: python scripts/load_test.py --concurrency 5  (chạy đến T+2:15)
T+2:10  Thành-viên-#3: verify traces trên Langfuse (cần ≥ 10)
T+2:15  Thành-viên-#1: python scripts/inject_incident.py --scenario rag_slow
        → ghi lại symptoms (latency tăng)
        → tắt incident → ghi lại recovery
T+2:20  Thành-viên-#4: chạy dashboard script, chụp screenshot
T+2:30  Chạy validate_logs.py lần cuối → score ≥ 80
```

---

## PHASE 4 — Evidence & Report (T+2:30 → T+2:50)

**Thành-viên-#4** điều phối, từng người cung cấp:
- Screenshot correlation_id trong log → Thành-viên-#1
- Screenshot PII redaction → Thành-viên-#2
- Screenshot Langfuse trace waterfall (≥10 traces) → Thành-viên-#3
- Screenshot dashboard 6 panels → Thành-viên-#4
- Link commit/PR của mình → từng người

Điền vào `docs/blueprint-template.md` và `docs/grading-evidence.md`.

---

## PHASE 5 — Demo Prep (T+2:50 → T+3:00)

- Mỗi người trình bày phần mình implement:
  - Thành-viên-#1: giải thích correlation ID flow
  - Thành-viên-#2: giải thích PII scrubbing pipeline
  - Thành-viên-#3: giải thích SLO + trace waterfall
  - Thành-viên-#4: giải thích 6 dashboard panels + incident story

---

## Điều kiện pass

- [ ] `validate_logs.py` score ≥ 80/100
- [ ] ≥ 10 traces trên Langfuse
- [ ] Dashboard đủ 6 panels
- [ ] `docs/blueprint-template.md` đầy đủ tên 4 thành viên
- [ ] Mỗi thành viên có ≥ 2 commits trên branch riêng

---

## Liên lạc khẩn

Nếu bị block > 10 phút, ping nhóm chat ngay — đừng tự cố một mình.
