# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Nhóm 9 — Day 13 Observability

- [REPO_URL]: [Link GitHub](https://github.com/DangMinh21/Lab13-Observability)

- [MEMBERS]:
  - Member A: Nguyễn Quang Tùng | Role: Correlation ID & Incident Debug
  - Member B: Nguyễn Thị Quỳnh Trang | Role: Logging & PII Scrubbing
  - Member C: Đặng Văn Minh | Role: Tracing (Langfuse) + SLO + Alerts
  - Member D: Đồng Văn Thịnh | Role: Dashboard + Docs + Report

---

## 2. Group Performance (Auto-Verified)
- VALIDATE_LOGS_FINAL_SCORE: 100/100
- TOTAL_TRACES_COUNT: 214
- PII_LEAKS_FOUND: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- EVIDENCE_CORRELATION_ID_SCREENSHOT: docs/screenshots/correlation-id-log.png
- EVIDENCE_PII_REDACTION_SCREENSHOT: docs/screenshots/pii-redaction-log.png
- EVIDENCE_TRACE_WATERFALL_SCREENSHOT: docs/screenshots/langfuse-trace-waterfall.png
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

### 3.3 Alerting & Runbook
- DASHBOARD_6_PANELS_SCREENSHOT: [docs/screenshots/01_dashboard_normal.png](docs/screenshots/01_dashboard_normal.png)
- ALERT_RULES_SCREENSHOT: [docs/screenshots/02_dashboard_breach.png](docs/screenshots/02_dashboard_breach.png)
- SAMPLE_RUNBOOK_LINK: [docs/screenshots/before_and_after_ragSlow.png](docs/screenshots/before_and_after_ragSlow.png)

---

## 4. Incident Response (Group)
- SCENARIO_NAME: rag_slow
- SYMPTOMS_OBSERVED: Latency P95 tăng vọt từ ~164ms lên > 3600ms, vi phạm SLO nghiêm trọng.
- ROOT_CAUSE_PROVED_BY: Langfuse trace waterfall cho thấy sự gia tăng đột biến trong thời gian xử lý của span 'retrieve'.
- FIX_ACTION: Thực hiện POST /incidents/rag_slow/disable để vô hiệu hóa script tiêm trễ, đưa hệ thống về trạng thái bình thường.
- PREVENTIVE_MEASURE: Thiết lập alert rule 'high_latency_p95' trong Prometheus/Langfuse để cảnh báo khi P95 vượt quá 2000ms.

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_C_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### Đồng Văn Thịnh
- [TASKS_COMPLETED]: Xây dựng terminal dashboard 6 panels kết nối với endpoint /metrics. Điều phối file blueprint-template.md và quản lý evidence. Thiết lập thư mục docs/screenshots và checklist pass demo. Tối ưu UI Dashboard với single-column layout cho khả năng quan sát tốt hơn.
- [EVIDENCE_LINK]: https://github.com/DangMinh21/Lab13-Observability/pull/4

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Sử dụng mô hình Claude-Sonnet-4-5 với chiến thuật summarize prompt để tiết kiệm input tokens.
- [BONUS_CUSTOM_METRIC]: Triển khai Heuristic Quality Score (0.0 - 1.0) để đo lường độ tin cậy của phản hồi LLM theo thời gian thực.
