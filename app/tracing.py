from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import observe, get_client

    class _LangfuseContextCompat:
        """Compatibility shim: v2 API → v3.
        update_current_trace works via get_client(); update_current_observation is a no-op (removed in v3).
        """
        def update_current_trace(self, **kwargs: Any) -> None:
            get_client().update_current_trace(**kwargs)

        def update_current_observation(self, **kwargs: Any) -> None:
            # update_current_observation was removed in Langfuse v3; metadata captured via @observe
            pass

        def flush(self) -> None:
            get_client().flush()

    langfuse_context = _LangfuseContextCompat()
    print("[tracing] Langfuse v3 initialized OK")

    def flush_traces() -> None:
        print("[tracing] Flushing traces...")
        get_client().flush()
        print("[tracing] Flush complete.")

except Exception as _exc:  # pragma: no cover
    print(f"[tracing] WARNING: Langfuse import failed: {_exc}")
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()

    def flush_traces() -> None:
        return None


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
