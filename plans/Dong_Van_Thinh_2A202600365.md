# Kế hoạch cá nhân — Thành-viên-#4

**Role**: Dashboard + Docs + Report Coordinator  
**Branch**: `feature/tv4/dashboard-docs`

---

## Tại sao role này quan trọng

Dashboard là 10 điểm kỹ thuật + ảnh hưởng lớn đến Live Demo (20 điểm). Thành-viên-#4 còn điều phối toàn bộ `blueprint-template.md` — nếu thiếu tên thành viên hoặc evidence, nhóm mất điểm cá nhân. Đây là người giữ "bức tranh toàn cảnh" của team.

---

## Timeline cá nhân

| Thời gian | Việc làm |
|---|---|
| T+0:00 → T+0:15 | Setup: clone, virtualenv, pip install, tạo branch |
| T+0:15 → T+0:45 | Điền metadata nhóm vào `docs/blueprint-template.md` |
| T+0:45 → T+1:30 | Viết `scripts/dashboard.py`, khám phá `/metrics` endpoint |
| T+1:30 → T+2:00 | Chờ merge PRs — review PR của Thành-viên-#1 hoặc #2 |
| T+2:00 → T+2:30 | Chạy dashboard, chụp screenshot 6 panels khi có data |
| T+2:30 → T+2:50 | Thu thập evidence từ cả nhóm, hoàn thiện blueprint |
| T+2:50 → T+3:00 | Điều phối demo prep, kiểm tra checklist pass |

---

## Nhiệm vụ kỹ thuật chi tiết

### 1. Điền metadata nhóm vào `docs/blueprint-template.md` (T+0:15 → T+0:45)

```markdown
## 1. Team Metadata
- [GROUP_NAME]: Nhóm X — Day 13 Observability
- [REPO_URL]: https://github.com/<org>/<repo>
- [MEMBERS]:
  - Member A: <Thành-viên-#1> | Role: Correlation ID & Incident Debug
  - Member B: <Thành-viên-#2> | Role: Logging & PII Scrubbing
  - Member C: <Thành-viên-#3> | Role: Tracing (Langfuse) + SLO + Alerts
  - Member D: <Thành-viên-#4> | Role: Dashboard + Docs + Report
```

Tạo folder screenshots:
```bash
mkdir -p docs/screenshots
```

### 2. Viết `scripts/dashboard.py` — dashboard terminal (T+0:45 → T+1:30)

```python
"""Simple dashboard that polls /metrics and displays in terminal."""
import time, requests, os

BASE = os.getenv("APP_URL", "http://localhost:8000")

def render():
    try:
        m = requests.get(f"{BASE}/metrics", timeout=2).json()
    except Exception as e:
        print(f"Error: {e}")
        return

    print("\033[2J\033[H")  # clear screen
    print("=" * 55)
    print("  Day 13 Observability Dashboard")
    print("=" * 55)
    print(f"  [1] Latency (ms)   P50:{m['latency_p50']:>7.0f}  "
          f"P95:{m['latency_p95']:>7.0f}  P99:{m['latency_p99']:>7.0f}")
    print(f"      SLO: P95 < 3000ms  {'OK' if m['latency_p95'] < 3000 else 'BREACH':>6}")
    print(f"  [2] Traffic        {m['traffic']:>7} requests total")
    total = m['traffic'] or 1
    err_count = sum(m['error_breakdown'].values())
    err_rate = err_count / total * 100
    print(f"  [3] Error Rate     {err_rate:>7.2f}%  "
          f"({'OK' if err_rate < 2 else 'BREACH'})")
    print(f"  [4] Cost           avg ${m['avg_cost_usd']:>8.4f}  "
          f"total ${m['total_cost_usd']:>8.4f}")
    print(f"  [5] Tokens         in:{m['tokens_in_total']:>8}  out:{m['tokens_out_total']:>8}")
    print(f"  [6] Quality Avg    {m['quality_avg']:>7.4f}  "
          f"({'OK' if m['quality_avg'] >= 0.75 else 'LOW'})")
    print("=" * 55)
    print(f"  Last updated: {time.strftime('%H:%M:%S')}  (refresh 15s)")

while True:
    render()
    time.sleep(15)
```

```bash
python scripts/dashboard.py
# Dashboard tự refresh mỗi 15 giây
# Chụp screenshot sau khi có data từ load test
```

### 3. Hoàn thiện `docs/blueprint-template.md` (T+2:30 → T+2:50)

Thu thập từ từng thành viên và điền:

```markdown
## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: <kết quả validate_logs.py>/100
- [TOTAL_TRACES_COUNT]: <xem trên Langfuse>
- [PII_LEAKS_FOUND]: 0

## 3. Technical Evidence (Group)
### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/screenshots/correlation-id-log.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/screenshots/pii-redaction-log.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/screenshots/langfuse-trace-waterfall.png
- [TRACE_WATERFALL_EXPLANATION]: (Thành-viên-#3 cung cấp)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/screenshots/dashboard-6-panels.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | <giá trị đo> ms |
| Error Rate | < 2% | 28d | <giá trị đo> % |
| Cost Budget | < $2.5/day | 1d | $<giá trị đo> |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: docs/screenshots/alert-rules.png
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#4-quality-degradation

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: latency_p95 tăng từ ~300ms lên ~2500ms sau khi enable incident
- [ROOT_CAUSE_PROVED_BY]: Langfuse trace — span "retrieve" chiếm 85% tổng latency
- [FIX_ACTION]: POST /incidents/rag_slow/disable → latency trở về bình thường
- [PREVENTIVE_MEASURE]: Alert high_latency_p95 trigger sau 30m sustained breach
```

---

## Checklist pass cuối buổi (Thành-viên-#4 phụ trách kiểm tra)

```
[ ] validate_logs.py score ≥ 80/100
[ ] ≥ 10 traces trên Langfuse
[ ] Dashboard có đủ 6 panels — đã chụp screenshot
[ ] blueprint-template.md có tên cả 4 người
[ ] Mỗi thành viên có link commit/PR trong blueprint
[ ] docs/screenshots/ có ≥ 5 ảnh evidence
[ ] Tất cả 4 PRs đã merge vào main
[ ] App chạy được trên main branch
```

---

## Git workflow

```bash
# Setup branch
git checkout -b feature/tv4/dashboard-docs

git add docs/blueprint-template.md
git commit -m "docs: fill team metadata and member roles in blueprint"

git add scripts/dashboard.py
git commit -m "feat(dashboard): add terminal dashboard polling /metrics endpoint"

git add docs/screenshots/
git commit -m "docs: add evidence screenshots for grading"

git add docs/blueprint-template.md docs/grading-evidence.md
git commit -m "docs: complete blueprint report with all evidence links"

git push -u origin feature/tv4/dashboard-docs
# PR title: "docs: complete dashboard, screenshots, and team report"
```

---

## Evidence cần thu thập

- [ ] Screenshot dashboard 6 panels khi có data (sau load test)
- [ ] Output cuối của `validate_logs.py` (terminal)
- [ ] Screenshot `config/alert_rules.yaml` với 4 rules
- [ ] Link PR đã merge

---

## Phần điền trong `docs/blueprint-template.md`

```
### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: Build terminal dashboard 6 panels polling /metrics. Điều phối blueprint-template.md và evidence collection. Tạo docs/screenshots/ với đầy đủ ảnh. Kiểm tra checklist pass trước demo.
- [EVIDENCE_LINK]: <link PR>
```

---

## Câu hỏi giảng viên có thể hỏi

1. 6 panels dashboard đo gì, tại sao chọn 6 này?  
   → Latency (SLO), Traffic (volume), Error Rate (reliability), Cost (budget), Tokens (usage), Quality (output) — đủ 4 Golden Signals cộng thêm AI-specific (cost, quality).

2. Tại sao cần SLO line trên dashboard?  
   → Để on-call engineer nhìn vào biết ngay panel nào đang breach mà không cần nhớ threshold. Giảm MTTD (Mean Time to Detect).

3. Dashboard refresh 15 giây có đủ nhanh không?  
   → Với in-memory metrics này thì đủ. Production cần Prometheus scrape mỗi 15s + Grafana realtime cho incident P1.
