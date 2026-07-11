"""Tests for the DAG definition model and topological sort.

These tests are pure Python — no database or async fixtures needed.
"""

import pytest
from app.engine.dag import WorkflowDag, topological_sort


class TestWorkflowDag:
    """Test suite for WorkflowDag data model + topological_sort."""

    # ------------------------------------------------------------------
    # topological_sort
    # ------------------------------------------------------------------

    def test_linear_dag(self):
        """Verify topological sort of a linear DAG: n1 -> n2 -> n3."""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {}},
                {"id": "n2", "type": "llm", "config": {}},
                {"id": "n3", "type": "output", "config": {}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        )
        levels = topological_sort(dag)
        assert len(levels) == 3
        assert levels[0][0]["id"] == "n1"
        assert levels[1][0]["id"] == "n2"
        assert levels[2][0]["id"] == "n3"

    def test_branching_dag(self):
        """Verify topological sort of a branching DAG: n1 -> n2, n1 -> n3."""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {}},
                {"id": "n2", "type": "llm", "config": {}},
                {"id": "n3", "type": "llm", "config": {}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n1", "target": "n3"},
            ],
        )
        levels = topological_sort(dag)
        assert len(levels) == 2  # n1, then n2+n3
        assert levels[0][0]["id"] == "n1"
        assert len(levels[1]) == 2  # n2 and n3 are parallel

    def test_cycle_dag_raises_error(self):
        """Verify that a cyclic DAG raises ValueError."""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input", "config": {}},
                {"id": "n2", "type": "llm", "config": {}},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n1"},  # cycle
            ],
        )
        with pytest.raises(ValueError, match="cycle"):
            topological_sort(dag)

    # ------------------------------------------------------------------
    # get_node
    # ------------------------------------------------------------------

    def test_get_node(self):
        """Verify get_node returns correct node or None."""
        dag = WorkflowDag(
            nodes=[{"id": "n1", "type": "input", "config": {}}],
            edges=[],
        )
        node = dag.get_node("n1")
        assert node["id"] == "n1"
        assert dag.get_node("nonexistent") is None

    # ------------------------------------------------------------------
    # get_upstream_nodes
    # ------------------------------------------------------------------

    def test_get_upstream_nodes(self):
        """Verify get_upstream_nodes returns all transitive upstream nodes."""
        dag = WorkflowDag(
            nodes=[
                {"id": "n1", "type": "input"},
                {"id": "n2", "type": "llm"},
                {"id": "n3", "type": "output"},
            ],
            edges=[
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        )
        upstream = dag.get_upstream_nodes("n3")
        assert len(upstream) == 2
        assert "n1" in [n["id"] for n in upstream]
        assert "n2" in [n["id"] for n in upstream]
