"""
Functions for generating A2A agent cards from SwissKnife agents.
"""

from typing import List
from AgentCrew.modules.agents import LocalAgent
from .common.types import AgentCard, AgentCapabilities, AgentSkill, AgentProvider


def map_tool_to_skill(tool_name: str, tool_def) -> AgentSkill:
    """
    Map a SwissKnife tool to an A2A skill.

    Args:
        tool_name: Name of the tool
        tool_def: Tool definition

    Returns:
        An A2A skill definition
    """
    # Extract description from tool definition if available
    description = "A tool capability"  # Default description
    if isinstance(tool_def, dict):
        if "description" in tool_def:
            description = tool_def["description"]
        elif "function" in tool_def and "description" in tool_def["function"]:
            description = tool_def["function"]["description"]

    return AgentSkill(
        id=tool_name,
        name=tool_name.replace("_", " ").title(),
        description=description,
        # Could add examples based on tool definition
        examples=None,
        # Most tools work with text input/output
        inputModes=["text/plain"],
        outputModes=["text/plain"],
        tags=[tool_name, "tool"],
    )


def create_agent_card(agent: LocalAgent, base_url: str) -> AgentCard:
    """
    Create an A2A agent card from a SwissKnife agent.

    Args:
        agent: The SwissKnife agent
        base_url: Base URL for the agent's endpoints

    Returns:
        An A2A agent card
    """
    # Map tools to skills
    skills: List[AgentSkill] = []
    try:
        for tool_name, (tool_def, _, _) in agent.tool_definitions.items():
            if callable(tool_def):
                # If it's a function, call it to get the definition
                try:
                    definition = tool_def()
                except Exception:
                    # If calling without provider fails, try with a default provider
                    definition = None
            else:
                definition = tool_def

            if definition:
                skill = map_tool_to_skill(tool_name, definition)
                skills.append(skill)
    except Exception:
        # If no tools available, add a basic skill
        skills = [
            AgentSkill(
                id="general",
                name="General Assistant",
                description="General purpose AI assistant",
                tags=["general", "assistant"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ]

    # Create capabilities based on agent features
    capabilities = AgentCapabilities(
        streaming=True,  # SwissKnife supports streaming
        pushNotifications=False,  # Not implemented yet
        stateTransitionHistory=True,  # SwissKnife tracks message history
    )

    # Create provider info
    provider = AgentProvider(
        organization="AgentCrew",
        url="https://github.com/daltonnyx/AgentCrew",
    )

    return AgentCard(
        name=agent.name if hasattr(agent, "name") else "AgentCrew Assistant",
        description=agent.description
        if hasattr(agent, "description")
        else "An AI assistant powered by AgentCrew",
        url=base_url,
        provider=provider,
        version="1.0.0",  # Should match AgentCrew version
        capabilities=capabilities,
        skills=skills,
        # Most SwissKnife agents work with text and files
        defaultInputModes=["text/plain", "application/octet-stream"],
        defaultOutputModes=["text/plain", "application/octet-stream"],
    )
