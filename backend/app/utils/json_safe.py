"""JSON-safe serialization helpers for arbitrary node outputs.

Node execution results — especially those produced by sandboxed data-analysis
code (pandas / numpy) — can contain scalar types the standard library ``json``
module cannot serialize: ``numpy.int64``, ``numpy.float64``, ``numpy.datetime64``,
``pandas.NA``, ``Decimal``, ``set``, ``bytes``, and so on. Persisting such values
into a SQLAlchemy ``JSON`` column (e.g. ``runs.output`` / ``runs.node_results``)
or returning them in an API response crashes with
``TypeError: Object of type X is not JSON serializable``.

:func:`make_json_safe` recursively converts any value into a JSON-serializable
Python tree. Unknown types fall back to ``str()`` so that *no* type can ever
escape serialization. :class:`SafeJSON` wraps this logic into a reusable
``JSON`` column type used by the ``Run`` model.
"""

from __future__ import annotations

import datetime as _dt
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, TypeDecorator


def make_json_safe(obj: Any) -> Any:
    """Recursively convert *obj* into a JSON-serializable structure."""
    # pandas sentinels / timestamps
    try:
        import pandas as _pd

        if hasattr(_pd, "NaT") and obj is _pd.NaT:
            return None
        if hasattr(_pd, "Timestamp") and isinstance(obj, _pd.Timestamp):
            return obj.isoformat()
        if getattr(_pd, "NA", None) is not None and obj is _pd.NA:
            return None
    except ImportError:
        pass

    # numpy scalars / arrays
    try:
        import numpy as _np

        # NOTE: np.timedelta64 is a subclass of np.integer in numpy 2.x, so it
        # must be checked before np.integer to avoid int(timedelta64) failures.
        if isinstance(obj, (_np.datetime64, _np.timedelta64)):
            return str(obj)
        if isinstance(obj, _np.integer):
            return int(obj)
        if isinstance(obj, _np.floating):
            return float(obj)
        if isinstance(obj, _np.bool_):
            return bool(obj)
        if isinstance(obj, _np.ndarray):
            return make_json_safe(obj.tolist())
    except ImportError:
        pass

    # standard python datetime / date
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()

    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, (set, frozenset)):
        return make_json_safe(list(obj))

    if isinstance(obj, (bytes, bytearray)):
        return obj.decode("utf-8", errors="replace")

    if isinstance(obj, dict):
        # JSON object keys must be strings; stringify every key.
        return {str(make_json_safe(k)): make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [make_json_safe(v) for v in obj]

    if isinstance(obj, float):
        import math as _math

        if _math.isnan(obj) or _math.isinf(obj):
            return None

    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    # Last resort: stringify anything we don't recognise, so that no value can
    # ever break JSON serialization downstream.
    return str(obj)


def json_dumps(obj: Any) -> str:
    """Safe ``json.dumps`` that never raises on exotic value types."""
    return json.dumps(make_json_safe(obj), ensure_ascii=False, default=str)


class SafeJSON(TypeDecorator):
    """``JSON`` column that sanitizes every bound value before persisting.

    Node outputs frequently contain numpy / pandas scalars; writing them into a
    plain ``JSON`` column crashes SQLAlchemy's serializer during ``flush()``.
    This type converts values through :func:`make_json_safe` first so that
    ``runs.input`` / ``runs.output`` / ``runs.node_results`` can never fail to
    serialize.
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        return make_json_safe(value)

    def process_result_value(self, value: Any, dialect) -> Any:
        return value
