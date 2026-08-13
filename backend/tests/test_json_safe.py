"""Tests for the JSON-safe serialization helpers.

Node execution results (especially from sandboxed data-analysis code) can
contain numpy / pandas scalars and other types the standard ``json`` module
cannot serialize. Storing such values into a SQLAlchemy JSON column (e.g.
``runs.output`` / ``runs.node_results``) previously crashed with
``TypeError: Object of type int64 is not JSON serializable``.

These tests pin down that :func:`make_json_safe` and the :class:`SafeJSON`
column type convert every such value into a JSON-serializable structure.
"""

import asyncio
import datetime
import decimal
import json

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import Column, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.utils.json_safe import SafeJSON, json_dumps, make_json_safe


class TestMakeJsonSafe:
    """make_json_safe must convert every exotic value into JSON-safe form."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (np.int64(5), 5),
            (np.uint64(7), 7),
            (np.float64(1.5), 1.5),
            (np.bool_(True), True),
            (np.int32(-3), -3),
            (np.array([1, 2, 3]), [1, 2, 3]),
            (np.datetime64("2025-01-01"), "2025-01-01"),
            (np.timedelta64(5, "D"), "5 days"),
            (pd.Timestamp("2025-01-01 10:30"), "2025-01-01T10:30:00"),
            (pd.NaT, None),
            (pd.NA, None),
            (datetime.datetime(2025, 1, 1, 10, 30), "2025-01-01T10:30:00"),
            (datetime.date(2025, 1, 1), "2025-01-01"),
            (decimal.Decimal("5.5"), 5.5),
            ({1, 2, 3}, [1, 2, 3]),
            (frozenset([1, 2]), [1, 2]),
            (b"abc", "abc"),
            (float("nan"), None),
            (float("inf"), None),
            (float("-inf"), None),
        ],
    )
    def test_scalar_conversion(self, value, expected):
        assert make_json_safe(value) == expected

    def test_nested_dict_conversion(self):
        raw = {
            "总销售额": np.int64(245500),
            "平均客单价": np.float64(40916.666666666664),
            "按日期": [{"销售额": np.int64(12500)}],
        }
        out = make_json_safe(raw)
        assert out["总销售额"] == 245500
        assert out["平均客单价"] == 40916.666666666664
        assert out["按日期"][0]["销售额"] == 12500

    def test_numpy_dict_keys_are_stringified(self):
        out = make_json_safe({np.int64(1): "x"})
        assert out == {"1": "x"}

    def test_tuple_converts_to_list(self):
        assert make_json_safe((1, np.int64(2))) == [1, 2]

    def test_unknown_object_falls_back_to_str(self):
        class Opaque:
            def __str__(self):
                return "<opaque>"

        assert make_json_safe(Opaque()) == "<opaque>"

    def test_json_dumps_never_raises(self):
        raw = {
            "总销售额": np.int64(245500),
            "日期": np.datetime64("2025-01-01"),
            "缺失": pd.NA,
            "集合": {np.int64(1), np.int64(2)},
        }
        # Should not raise TypeError
        json.loads(json_dumps(raw))


class TestSafeJSONColumn:
    """A JSON column backed by SafeJSON must persist exotic values."""

    def test_persists_numpy_values(self):
        Base = declarative_base()

        class Record(Base):
            __tablename__ = "safe_json_record"
            id = Column(String(36), primary_key=True)
            output = Column(SafeJSON)
            node_results = Column(SafeJSON)

        async def run():
            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            Session = sessionmaker(engine, class_=AsyncSession)
            db = Session()
            record = Record(
                id="test-1",
                output={
                    "总销售额": np.int64(245500),
                    "平均客单价": np.float64(40916.666666666664),
                    "日期": np.datetime64("2025-01-01"),
                },
                node_results=[
                    {"type": "node_done", "output": {"值": np.int64(42)}}
                ],
            )
            db.add(record)
            await db.flush()
            await db.commit()

            from sqlalchemy import select

            stored = (
                await db.execute(select(Record))
            ).scalar_one()
            assert stored.output["总销售额"] == 245500
            assert stored.output["平均客单价"] == 40916.666666666664
            assert stored.output["日期"] == "2025-01-01"
            assert stored.node_results[0]["output"]["值"] == 42
            await engine.dispose()

        asyncio.run(run())

    def test_null_values_are_safe(self):
        assert make_json_safe(None) is None
