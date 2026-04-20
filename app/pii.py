from __future__ import annotations

import hashlib
import re

# 1. Bổ sung đầy đủ các PII Patterns
PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone_vn": r"(?:\+84|0)[ \.-]?\d{3}[ \.-]?\d{3}[ \.-]?\d{3,4}",
    "cccd": r"\b\d{12}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "passport_vn": r"\b[A-Z]\d{7,8}\b",
    "address_vn": r"(?i)(số\s+\d+|đường\s+\w+|phường\s+\w+|quận\s+\w+|tỉnh\s+\w+)",
    "bank_account_vn": r"(?i)(?:stk|tài khoản|account)[^\d]*(\d{9,14})\b",
}

# 2. TỐI ƯU HÓA: Biên dịch sẵn các regex object để tăng tốc độ xử lý log
COMPILED_PATTERNS = {
    name: re.compile(pattern) 
    for name, pattern in PII_PATTERNS.items()
}


def scrub_text(text: str) -> str:
    if not text:
        return text
        
    safe = text
    for name, compiled_pattern in COMPILED_PATTERNS.items():
        safe = compiled_pattern.sub(f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    if not text:
        return ""
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    if not user_id:
        return ""
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]