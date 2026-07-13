"""ExcelParserNode 测试"""

import os
import pytest
import pandas as pd
from app.engine.context import ExecutionContext
from app.nodes.excel_parser import ExcelParserNodeExecutor


@pytest.fixture
def sample_excel(tmp_path):
    """创建测试 Excel 文件"""
    df = pd.DataFrame({"城市": ["北京", "上海", "广州"], "销售额": [100, 200, 150], "年份": [2024, 2024, 2024]})
    path = tmp_path / "test.xlsx"
    df.to_excel(path, index=False)
    return str(path)


@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "test.csv"
    with open(path, "w", encoding="utf-8") as f:
        f.write("城市,销售额,年份\n北京,100,2024\n上海,200,2024\n")
    return str(path)


class TestExcelParserNode:
    def test_parse_xlsx(self, sample_excel):
        ctx = ExecutionContext({})
        executor = ExcelParserNodeExecutor()
        result = executor.execute(ctx, {"file_path": sample_excel})
        assert result["row_count"] == 3
        assert "城市" in result["columns"]
        assert "data_text" in result
        assert "北京" in result["data_text"]

    def test_parse_csv(self, sample_csv):
        ctx = ExecutionContext({})
        executor = ExcelParserNodeExecutor()
        result = executor.execute(ctx, {"file_path": sample_csv})
        assert result["row_count"] == 2
        assert result["columns"] == ["城市", "销售额", "年份"]

    def test_preview_rows(self, sample_excel):
        ctx = ExecutionContext({})
        executor = ExcelParserNodeExecutor()
        result = executor.execute(ctx, {"file_path": sample_excel, "max_rows": 2})
        assert result["display_rows"] == 2

    def test_file_not_found(self):
        ctx = ExecutionContext({})
        executor = ExcelParserNodeExecutor()
        result = executor.execute(ctx, {"file_path": "/nonexistent.xlsx"})
        assert "error" in result

    def test_empty_config(self):
        ctx = ExecutionContext({})
        executor = ExcelParserNodeExecutor()
        result = executor.execute(ctx, {})
        assert "error" in result

    def test_sheet_names(self, sample_excel):
        names = ExcelParserNodeExecutor._get_sheet_names(sample_excel)
        assert "Sheet1" in names

    def test_preview_structure(self, sample_excel):
        ctx = ExecutionContext({})
        executor = ExcelParserNodeExecutor()
        result = executor.execute(ctx, {"file_path": sample_excel})
        assert isinstance(result["preview"], list)
        assert len(result["preview"]) > 0
        assert "城市" in result["preview"][0]

    def test_summary_string(self, sample_excel):
        ctx = ExecutionContext({})
        executor = ExcelParserNodeExecutor()
        result = executor.execute(ctx, {"file_path": sample_excel})
        assert "3" in result["summary"]
        assert "3" in str(result["row_count"])
