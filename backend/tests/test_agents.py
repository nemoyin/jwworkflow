"""Tests for scenario-specific AI agents."""

import asyncio

import pytest

from app.schemas.tool import ToolDefinition as ToolDefSchema
from app.agents import (
    ComplianceAgent,
    CollusionAgent,
    InterviewAgent,
    BaseScenarioAgent,
    get_agent,
    list_agents,
    get_all_tool_definitions,
)


# ===========================================================================
# BaseScenarioAgent
# ===========================================================================


class TestBaseScenarioAgent:
    """Test the base agent abstract class contract."""

    def test_abstract_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            BaseScenarioAgent()  # type: ignore[abstract]

    def test_concrete_agent_implements_all_abstract_members(self):
        """Each built-in agent should implement name, description, execute."""
        for cls in (ComplianceAgent, CollusionAgent, InterviewAgent):
            agent = cls()
            assert isinstance(agent.name, str) and agent.name
            assert isinstance(agent.description, str) and agent.description
            assert callable(agent.execute)


# ===========================================================================
# ComplianceAgent
# ===========================================================================


class TestComplianceAgent:
    """Tests for 招标合规审查 Agent."""

    @pytest.fixture
    def agent(self):
        return ComplianceAgent()

    def test_name_and_description(self, agent):
        assert agent.name == "compliance"
        assert len(agent.description) > 10

    def test_execute_empty_params(self, agent):
        result = asyncio.run(agent.execute({}))
        assert "error" in result
        assert "document_text" in result["error"]

    def test_execute_returns_expected_structure(self, agent):
        result = asyncio.run(
            agent.execute({"document_text": "招标文件示例内容"})
        )
        assert "score" in result
        assert isinstance(result["score"], float)
        assert 0.0 <= result["score"] <= 1.0

        assert "issues" in result
        assert isinstance(result["issues"], list)
        assert len(result["issues"]) > 0

        issue = result["issues"][0]
        assert "type" in issue
        assert "description" in issue
        assert "severity" in issue
        assert issue["severity"] in ("high", "medium", "low")

    def test_execute_issues_have_valid_severity(self, agent):
        result = asyncio.run(
            agent.execute({"document_text": "测试文件"})
        )
        valid_severities = {"high", "medium", "low"}
        for issue in result["issues"]:
            assert issue["severity"] in valid_severities
            assert isinstance(issue["description"], str)
            assert len(issue["description"]) > 0

    @pytest.mark.asyncio
    async def test_async_execute(self, agent):
        result = await agent.execute({"document_text": "async test"})
        assert "score" in result

    def test_input_schema_requires_document_text(self, agent):
        schema = agent._input_schema()
        assert "required" in schema
        assert "document_text" in schema["required"]


# ===========================================================================
# CollusionAgent
# ===========================================================================


class TestCollusionAgent:
    """Tests for 围串标分析 Agent."""

    @pytest.fixture
    def agent(self):
        return CollusionAgent()

    def test_name_and_description(self, agent):
        assert agent.name == "collusion"
        assert len(agent.description) > 10

    def test_execute_empty_params(self, agent):
        result = asyncio.run(agent.execute({}))
        assert "error" in result
        assert "bidder_list" in result["error"]

    def test_execute_returns_expected_structure(self, agent):
        bidders = [
            {"name": "甲公司", "credit_code": "911111111111111111"},
            {"name": "乙公司", "credit_code": "922222222222222222"},
            {"name": "丙公司", "credit_code": "933333333333333333"},
            {"name": "丁公司", "credit_code": "944444444444444444"},
        ]
        result = asyncio.run(
            agent.execute({"bidder_list": bidders})
        )

        assert "risk_level" in result
        assert result["risk_level"] in ("high", "medium", "low")

        assert "indicators" in result
        assert isinstance(result["indicators"], list)
        assert len(result["indicators"]) > 0

        indicator = result["indicators"][0]
        assert "type" in indicator
        assert "description" in indicator
        assert "confidence" in indicator
        assert 0.0 <= indicator["confidence"] <= 1.0
        assert "involved_parties" in indicator

    def test_execute_with_two_bidders(self, agent):
        """Should still work with minimal bidder list."""
        bidders = [
            {"name": "投标人X"},
            {"name": "投标人Y"},
        ]
        result = asyncio.run(
            agent.execute({"bidder_list": bidders})
        )
        assert "risk_level" in result

    def test_indicators_reference_bidder_names(self, agent):
        bidders = [
            {"name": "Alpha Corp"},
            {"name": "Beta Ltd"},
            {"name": "Gamma Inc"},
            {"name": "Delta LLC"},
        ]
        result = asyncio.run(
            agent.execute({"bidder_list": bidders})
        )
        for indicator in result["indicators"]:
            for party in indicator["involved_parties"]:
                assert any(party == b["name"] for b in bidders) or party in (
                    "投标人C", "投标人D"
                )

    def test_input_schema_requires_bidder_list(self, agent):
        schema = agent._input_schema()
        assert "required" in schema
        assert "bidder_list" in schema["required"]


# ===========================================================================
# InterviewAgent
# ===========================================================================


class TestInterviewAgent:
    """Tests for 纪检谈话 Agent."""

    @pytest.fixture
    def agent(self):
        return InterviewAgent()

    def test_name_and_description(self, agent):
        assert agent.name == "interview"
        assert len(agent.description) > 10

    def test_execute_empty_params(self, agent):
        result = asyncio.run(agent.execute({}))
        assert "error" in result
        assert "question" in result["error"]

    def test_execute_returns_expected_structure(self, agent):
        result = asyncio.run(
            agent.execute({"question": "请说明你在该项目中的具体职责？"})
        )
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

        # Stub also returns emotional_state
        assert "emotional_state" in result
        assert isinstance(result["emotional_state"], str)

    def test_execute_with_context(self, agent):
        result = asyncio.run(
            agent.execute({
                "question": "你认识投标方的人吗？",
                "context": {
                    "interviewee_name": "张三",
                    "interviewee_role": "招标专员",
                },
            })
        )
        assert "response" in result
        assert "张三" in result["response"]

    def test_execute_without_context(self, agent):
        result = asyncio.run(
            agent.execute({"question": "请陈述经过。"})
        )
        assert "response" in result
        assert len(result["response"]) > 10

    def test_input_schema_requires_question(self, agent):
        schema = agent._input_schema()
        assert "required" in schema
        assert "question" in schema["required"]


# ===========================================================================
# Tool Definition Integration
# ===========================================================================


class TestToolDefinitionIntegration:
    """Tests that each agent correctly produces ToolDefinition objects."""

    def test_to_tool_definition_returns_valid_tool_def(self):
        for agent_cls in (ComplianceAgent, CollusionAgent, InterviewAgent):
            agent = agent_cls()
            tool_def = agent.to_tool_definition()

            assert isinstance(tool_def, ToolDefSchema)
            assert tool_def.name == agent.name
            assert tool_def.description == agent.description
            assert tool_def.method == "POST"
            assert agent.name in tool_def.endpoint
            assert isinstance(tool_def.input_schema, dict)

    def test_to_tool_definition_endpoint_format(self):
        compliance = ComplianceAgent()
        tool_def = compliance.to_tool_definition()
        assert tool_def.endpoint == (
            "http://localhost:8000/api/v1/agents/compliance"
        )

    def test_each_agent_has_unique_endpoint(self):
        endpoints = set()
        for agent_cls in (ComplianceAgent, CollusionAgent, InterviewAgent):
            tool_def = agent_cls().to_tool_definition()
            assert tool_def.endpoint not in endpoints
            endpoints.add(tool_def.endpoint)
        assert len(endpoints) == 3


# ===========================================================================
# Registry
# ===========================================================================


class TestAgentRegistry:
    """Tests for the agent registry functions."""

    def test_get_agent_returns_instance(self):
        for name in ("compliance", "collusion", "interview"):
            agent = get_agent(name)
            assert isinstance(agent, BaseScenarioAgent)
            assert agent.name == name

    def test_get_agent_unknown(self):
        with pytest.raises(KeyError, match="foo"):
            get_agent("foo")

    def test_list_agents_returns_all(self):
        agents = list_agents()
        assert isinstance(agents, list)
        assert len(agents) == 3

        names = [n for n, _ in agents]
        assert "compliance" in names
        assert "collusion" in names
        assert "interview" in names

        for _, desc in agents:
            assert isinstance(desc, str)
            assert len(desc) > 10

    def test_get_all_tool_definitions(self):
        tool_defs = get_all_tool_definitions()
        assert len(tool_defs) == 3

        names = {t.name for t in tool_defs}
        assert names == {"compliance", "collusion", "interview"}


# ===========================================================================
# Async execution (pytest-asyncio)
# ===========================================================================


@pytest.mark.asyncio
class TestAsyncExecution:
    """Tests using pytest-asyncio marker for proper async execution."""

    @pytest.mark.parametrize("agent_cls", [
        ComplianceAgent,
        CollusionAgent,
        InterviewAgent,
    ])
    async def test_async_execute_returns_dict(self, agent_cls):
        agent = agent_cls()
        params = {}
        if agent.name == "compliance":
            params = {"document_text": "test"}
        elif agent.name == "collusion":
            params = {"bidder_list": [{"name": "A"}, {"name": "B"}]}
        elif agent.name == "interview":
            params = {"question": "test?"}

        result = await agent.execute(params)
        assert isinstance(result, dict)
