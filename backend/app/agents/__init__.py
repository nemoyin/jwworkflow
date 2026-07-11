"""Scenario-specific AI agent registry.

Provides a framework for wrapping existing scenario-specific AI agents as
pluggable tools that can be used by the Agent node.

Usage
-----
::

    from app.agents import ComplianceAgent, CollusionAgent, InterviewAgent
    from app.agents import get_agent, list_agents

    agents = list_agents()          # [(name, description), ...]
    agent  = get_agent("compliance") # ComplianceAgent instance
    tool   = agent.to_tool_definition()  # ToolDefinition for Agent node
    result = await agent.execute(params)
"""

from app.agents.base_agent import BaseScenarioAgent, ToolDefinition
from app.agents.compliance_agent import ComplianceAgent
from app.agents.collusion_agent import CollusionAgent
from app.agents.interview_agent import InterviewAgent

# ---------------------------------------------------------------------------
# Built-in agent registry
# ---------------------------------------------------------------------------
_BUILTIN_AGENTS: dict[str, type[BaseScenarioAgent]] = {
    "compliance": ComplianceAgent,
    "collusion": CollusionAgent,
    "interview": InterviewAgent,
}


def get_agent(name: str) -> BaseScenarioAgent:
    """Get an agent instance by name.

    Parameters
    ----------
    name : str
        Agent name (e.g. ``"compliance"``, ``"collusion"``, ``"interview"``).

    Returns
    -------
    BaseScenarioAgent
        A fresh instance of the requested agent.

    Raises
    ------
    KeyError
        If the agent name is not registered.
    """
    if name not in _BUILTIN_AGENTS:
        raise KeyError(
            f"Unknown agent: {name!r}. "
            f"Available: {list(_BUILTIN_AGENTS.keys())}"
        )
    return _BUILTIN_AGENTS[name]()


def list_agents() -> list[tuple[str, str]]:
    """List all registered scenario agents.

    Returns
    -------
    list[tuple[str, str]]
        List of ``(name, description)`` pairs.
    """
    result = []
    for name, cls in _BUILTIN_AGENTS.items():
        instance = cls()
        result.append((instance.name, instance.description))
    return result


def get_all_tool_definitions() -> list[ToolDefinition]:
    """Get ToolDefinition for every registered agent.

    Returns
    -------
    list[ToolDefinition]
        Tool definitions suitable for injecting into an Agent node config.
    """
    return [
        cls().to_tool_definition()
        for cls in _BUILTIN_AGENTS.values()
    ]


__all__ = [
    "BaseScenarioAgent",
    "ComplianceAgent",
    "CollusionAgent",
    "InterviewAgent",
    "ToolDefinition",
    "get_agent",
    "list_agents",
    "get_all_tool_definitions",
]
