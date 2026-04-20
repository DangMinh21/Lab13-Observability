from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_auto_generates_correlation_id():
    """Không gửi x-request-id → server tự sinh theo format req-<8hex>"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    req_id = response.headers.get("x-request-id", "")
    assert req_id.startswith("req-"), f"Expected req-<hex>, got: {req_id}"
    assert len(req_id) == 12  # "req-" (4) + 8 hex chars


@pytest.mark.anyio
async def test_echoes_provided_correlation_id():
    """Gửi x-request-id tùy chỉnh → server phải trả lại đúng ID đó"""
    custom_id = "my-custom-id-123"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health", headers={"x-request-id": custom_id})

    assert response.headers.get("x-request-id") == custom_id


@pytest.mark.anyio
async def test_response_time_header_present():
    """x-response-time-ms phải có và là số hợp lệ"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    elapsed = response.headers.get("x-response-time-ms")
    assert elapsed is not None
    assert float(elapsed) >= 0
