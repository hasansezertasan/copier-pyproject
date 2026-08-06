"""The redis_backend chaining fix.

A redis-*broker* worker (``redis_enabled`` true via the broker, ``include_redis``
false) must honor ``redis_backend=valkey`` in the devcontainer compose — the
image/CLI are gated on ``redis_enabled``, not ``include_redis``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable


def _compose(root: Path) -> str:
    return (root / ".devcontainer" / "docker-compose.yml").read_text()


def test_redis_broker_worker_honors_valkey(render: Callable[..., Path]) -> None:
    compose = _compose(
        render(
            preset="library",
            include_worker=True,
            worker_broker="redis",
            include_redis=False,
            redis_backend="valkey",
        )
    )
    assert "valkey/valkey:8" in compose
    assert "valkey-cli" in compose


def test_normal_redis_stays_redis(render: Callable[..., Path]) -> None:
    compose = _compose(
        render(preset="library", include_redis=True, redis_backend="redis")
    )
    assert "redis:7" in compose
    assert "valkey" not in compose
