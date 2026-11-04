"""ECC Component Execution Runner.

Provides callable programmatic interfaces for Agents, Skills, Rules, and Commands.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os
import subprocess

from core.model_router.router import ROUTER
from core.model_router.schemas import CompletionRequest, ChatMessage
from .registry import ECC_REGISTRY, ECCRegistry


@dataclass
class AgentExecutionResult:
    """Result of calling an ECC agent."""
    agent_name: str
    output: str
    success: bool
    provider: str = ""
    model: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillExecutionResult:
    """Result of running or applying an ECC skill."""
    skill_name: str
    output: str
    success: bool
    is_script: bool = False
    exit_code: int = 0
    error: Optional[str] = None


@dataclass
class CommandExecutionResult:
    """Result of executing an ECC command."""
    command_name: str
    output: str
    success: bool
    error: Optional[str] = None


class ECCRunner:
    """Execution engine for ECC components."""

    def __init__(self, registry: Optional[ECCRegistry] = None, router=None):
        self.registry = registry or ECC_REGISTRY
        self.router = router or ROUTER

    async def call_agent(
        self,
        agent_name: str,
        user_prompt: str,
        context: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AgentExecutionResult:
        """Execute a specialized ECC agent with its full persona and instructions."""
        agent = self.registry.get_agent(agent_name)
        if not agent:
            return AgentExecutionResult(
                agent_name=agent_name,
                output="",
                success=False,
                error=f"Agent '{agent_name}' not found in registry.",
            )

        system_prompt = agent.system_instructions or agent.prompt
        if context:
            system_prompt = f"{system_prompt}\n\n## Project Context:\n{context}"

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        target_model = model or (agent.model if agent.model != "opus" else "default")
        req = CompletionRequest(
            messages=messages,
            model=target_model,
            temperature=temperature,
        )

        try:
            resp = await self.router.generate(req)
            return AgentExecutionResult(
                agent_name=agent_name,
                output=resp.content,
                success=True,
                provider=resp.provider,
                model=resp.model,
                metadata={"tools": agent.tools, "usage": resp.usage},
            )
        except Exception as e:
            return AgentExecutionResult(
                agent_name=agent_name,
                output="",
                success=False,
                error=str(e),
            )

    async def run_skill(
        self,
        skill_name: str,
        script_name: Optional[str] = None,
        args: Optional[List[str]] = None,
    ) -> SkillExecutionResult:
        """Run a skill's script if available, or return its formatted instructions."""
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return SkillExecutionResult(
                skill_name=skill_name,
                output="",
                success=False,
                error=f"Skill '{skill_name}' not found in registry.",
            )

        # If a specific script is requested and exists
        if script_name and script_name in skill.scripts:
            script_path = os.path.join(skill.folder_path, "scripts", script_name)
            cmd = ["python", script_path] + (args or [])
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                return SkillExecutionResult(
                    skill_name=skill_name,
                    output=proc.stdout or proc.stderr,
                    success=proc.returncode == 0,
                    is_script=True,
                    exit_code=proc.returncode,
                    error=proc.stderr if proc.returncode != 0 else None,
                )
            except Exception as e:
                return SkillExecutionResult(
                    skill_name=skill_name,
                    output="",
                    success=False,
                    is_script=True,
                    error=str(e),
                )

        # If no script requested or not executable, return skill prompt instructions
        return SkillExecutionResult(
            skill_name=skill_name,
            output=skill.instructions,
            success=True,
            is_script=False,
        )

    def get_rules(
        self,
        suite_name: str,
        categories: Optional[List[str]] = None,
    ) -> str:
        """Retrieve formatted rules for a language or framework."""
        suite = self.registry.get_rule_suite(suite_name)
        if not suite:
            return ""

        formatted_rules = []
        for cat, content in suite.rules.items():
            if categories is None or cat in categories:
                formatted_rules.append(f"### Rule: {suite_name}/{cat}\n{content}")

        return "\n\n".join(formatted_rules)

    async def run_command(
        self,
        command_name: str,
        user_input: str = "",
        agent_name: str = "architect",
    ) -> CommandExecutionResult:
        """Execute an ECC command pipeline using the specified agent."""
        cmd = self.registry.get_command(command_name)
        if not cmd:
            return CommandExecutionResult(
                command_name=command_name,
                output="",
                success=False,
                error=f"Command '{command_name}' not found in registry.",
            )

        prompt = f"## Command Instructions for /{command_name}:\n{cmd.instructions}\n\nUser Input:\n{user_input}"
        res = await self.call_agent(agent_name=agent_name, user_prompt=prompt)
        return CommandExecutionResult(
            command_name=command_name,
            output=res.output,
            success=res.success,
            error=res.error,
        )


# Global singleton instance
ECC_RUNNER = ECCRunner(ECC_REGISTRY, ROUTER)
