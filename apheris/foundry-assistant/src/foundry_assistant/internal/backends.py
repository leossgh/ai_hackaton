"""Decision-backend selection, decoupled from config.

Callers pass the backend name and the gates file explicitly; this module never
reads config or the environment.

Decision backends:
  apheris-local - the fine-tuned on-premises model (server/serve_llamacpp.py),
                 reached over its /v1/systemone endpoint at APHERIS_LOCAL_URL unless
                 base_url says otherwise. The default: nothing leaves the premises.

Each backend emits confidence on its own scale, so each carries its own gates.
Prefer fitted gates from a gates file; the defaults here are
only a fallback.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from .walk import DEFAULT_GATES, Gates

APHERIS_LOCAL_URL = "http://127.0.0.1:8771"  # the model server's default port


def gates_for(backend: str, gates_file: Path | None = None) -> Gates:
    """Return fitted gates for a backend, falling back to the defaults.

    Args:
        backend: Backend name (apheris-local), or another gates key.
        gates_file: Optional JSON file of fitted gates keyed by backend.

    Returns:
        The Gates to use for this backend.
    """
    if gates_file and Path(gates_file).exists():
        fitted = json.loads(Path(gates_file).read_text()).get(backend)
        if fitted:
            # The file also carries fit/calibration metadata; keep
            # only the gate thresholds Gates accepts.
            fields = {f.name for f in dataclasses.fields(Gates)}
            return Gates(**{k: v for k, v in fitted.items() if k in fields})
    return DEFAULT_GATES


def make_client(
    backend: str,
    gates_file: Path | None = None,
    *,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[Any, Gates]:
    """Build the async client and gates for a backend.

    Args:
        backend: Backend name (apheris-local).
        gates_file: Optional JSON file of fitted gates.
        base_url: apheris-local's server URL (default APHERIS_LOCAL_URL).
        model: The model name apheris-local reports.

    Returns:
        Tuple of (async client context manager, Gates).

    Raises:
        ValueError: An unknown backend.
    """
    backend = backend.lower()
    gates = gates_for(backend, gates_file)

    if backend == "apheris-local":  # server/serve_llamacpp.py speaks /v1/systemone
        from .jeff_backend import JeffClient

        return JeffClient(base_url or APHERIS_LOCAL_URL, model or "apheris-local"), gates

    raise ValueError(f"unknown backend {backend!r} (apheris-local)")
