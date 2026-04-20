# Kế hoạch cá nhân — Thành-viên-#3

**Role**: Tracing (Langfuse) + SLO + Alerts  
**Branch**: `feature/tv3/tracing-slo-alerts`

---

## Tại sao role này quan trọng

- **Langfuse traces** là điều kiện pass bắt buộc (≥ 10 traces). Thiếu key = 0 traces.  
- **SLO + Alerts** là 10 điểm kỹ thuật riêng.  
- Cần **chia sẻ Langfuse keys** cho cả nhóm trước T+0:10 — đây là việc đầu tiên cần làm.

---

## Timeline cá nhân

| Thời gian | Việc làm |
|---|---|
| T+0:00 → T+0:10 | Tạo Langfuse project, lấy API keys, chia sẻ nhóm |
| T+0:10 → T+0:15 | Setup branch, pip install, cập nhật `.env` |
| T+0:15 → T+0:30 | Kiểm tra tracing hoạt động (gửi 1-2 test request) |
| T+0:30 → T+1:00 | Refine `config/slo.yaml` |
| T+1:00 → T+1:30 | Cập nhật `config/alert_rules.yaml` + `docs/alerts.md` |
| T+1:30 → T+1:50 | Commit, mở PR |
| T+2:00 → T+2:20 | Verify ≥ 10 traces trên Langfuse sau load test |
| T+2:30 → T+2:50 | Screenshot trace waterfall, điền blueprint |

---

## Nhiệm vụ kỹ thuật chi tiết

### 1. Setup Langfuse (T+0:00 → T+0:10)

**Bước 1**: Vào https://cloud.langfuse.com → Sign up / Login → Tạo project mới tên `day13-observability-lab`

**Bước 2**: Settings → API Keys → tạo key → copy:
- `LANGFUSE_PUBLIC_KEY=pk-lf-...`
- `LANGFUSE_SECRET_KEY=sk-lf-...`
- `LANGFUSE_HOST=https://cloud.langfuse.com`

**Bước 3**: Điền vào `.env` và chia sẻ vào nhóm chat ngay.

**Bước 4**: Kiểm tra nhanh:
```bash
uvicorn app.main:app --reload &
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","session_id":"s1","feature":"test","message":"hello langfuse"}'
# Lên Langfuse dashboard → Traces → phải thấy 1 trace mới
```

### 2. Refine `config/slo.yaml`

```yaml
service: day13-observability-lab
window: 28d
slis:
  latency_p95_ms:
    objective: 3000
    target: 99.5
    note: "Measured from /metrics endpoint latency_p95"
  error_rate_pct:
    objective: 2
    target: 99.0
    note: "Calculated as error_count / total_requests * 100"
  daily_cost_usd:
    objective: 2.50
    target: 100.0
    note: "Tracked via total_cost_usd from /metrics, reset daily"
  quality_score_avg:
    objective: 0.75
    target: 95.0
    note: "Heuristic score from agent._heuristic_quality()"
```

### 3. Cập nhật `config/alert_rules.yaml` — thêm alert thứ 4

```yaml
alerts:
  - name: high_latency_p95
    severity: P2
    condition: latency_p95_ms > 5000 for 30m
    type: symptom-based
    owner: team-oncall
    runbook: docs/alerts.md#1-high-latency-p95

  - name: high_error_rate
    severity: P1
    condition: error_rate_pct > 5 for 5m
    type: symptom-based
    owner: team-oncall
    runbook: docs/alerts.md#2-high-error-rate

  - name: cost_budget_spike
    severity: P2
    condition: hourly_cost_usd > 2x_baseline for 15m
    type: symptom-based
    owner: finops-owner
    runbook: docs/alerts.md#3-cost-budget-spike

  - name: quality_degradation
    severity: P2
    condition: quality_score_avg < 0.6 for 15m
    type: symptom-based
    owner: team-oncall
    runbook: docs/alerts.md#4-quality-degradation
```

### 4. Thêm runbook #4 vào `docs/alerts.md`

```markdown
## 4. Quality degradation
- Severity: P2
- Trigger: `quality_score_avg < 0.6 for 15m`
- Impact: users receive low-quality or irrelevant answers
- First checks:
  1. Open recent traces on Langfuse, filter by low quality_score
  2. Check RAG retrieval: doc_count = 0 means retrieval is failing
  3. Compare question vs answer tokens — short answers = likely LLM truncation
  4. Check if `llm_error` incident is active
- Mitigation:
  - retry retrieval with broader query
  - fallback to larger context window model
  - add minimum doc_count validation before LLM call
```

---

## Kiểm tra traces sau load test (T+2:00 → T+2:20)

```bash
curl http://localhost:8000/metrics | python -m json.tool
# Xem: traffic count

# Trên Langfuse dashboard:
# Traces → filter last 1h → đếm số traces
# Cần ≥ 10 traces với metadata đầy đủ:
# - user_id (hash), session_id
# - tags: ["lab", "<feature>", "claude-sonnet-4-5"]
```

---

## Git workflow

```bash
# Setup branch
git checkout -b feature/tv3/tracing-slo-alerts

git add .env
git commit -m "chore: add langfuse API keys to environment"

git add config/slo.yaml
git commit -m "feat(slo): refine SLI objectives and add notes"

git add config/alert_rules.yaml
git commit -m "feat(alerts): add quality_degradation alert rule"

git add docs/alerts.md
git commit -m "docs(alerts): add runbook for quality_degradation alert"

git push -u origin feature/tv3/tracing-slo-alerts
# PR title: "feat: configure Langfuse tracing, SLOs, and alert rules"
```

---

## Evidence cần thu thập

- [ ] Screenshot Langfuse trace list với ≥ 10 traces (cột user_id, session_id, tags)
- [ ] Screenshot 1 trace waterfall đầy đủ (spans: retrieve + llm.generate)
- [ ] Screenshot `config/alert_rules.yaml` với 4 rules
- [ ] Link PR đã merge

---

## Phần điền trong `docs/blueprint-template.md`

```
### [MEMBER_C_NAME]
- [TASKS_COMPLETED]: Setup Langfuse project và API keys. Refine SLO targets với ghi chú đo lường. Thêm alert rule quality_degradation. Viết runbook #4. Verify ≥ 10 traces với metadata đầy đủ.
- [EVIDENCE_LINK]: <link PR>
```

---

## Câu hỏi giảng viên có thể hỏi

1. SLO khác SLI như thế nào?  
   → SLI là chỉ số đo được (vd: latency_p95 = 2400ms). SLO là cam kết (vd: latency_p95 < 3000ms trong 99.5% thời gian 28 ngày).

2. Tại sao alert quality_degradation dùng `for 15m` chứ không `for 5m`?  
   → Quality score fluctuate tự nhiên theo loại query. 15 phút giảm liên tục mới là signal đáng tin, tránh false alert.

3. `@observe()` trong `agent.py` làm gì?  
   → Decorator của Langfuse tự động tạo một trace cho mỗi lần gọi hàm, record input/output, timing, và gửi lên cloud — không cần thay đổi logic code.
