"""ECC Component Tools for Payal Tool Registry.

Allows LLM and autonomous agents to query and invoke ECC agents, skills, rules, and commands.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field

from .base import BaseTool
from .schemas import PermissionLevel, ToolCategory, ToolResult
from integrations.ecc.registry import ECC_REGISTRY, ECCRegistry
from integrations.ecc.runner import ECC_RUNNER, ECCRunner


class CallECCAgentArgs(BaseModel):
    agent_name: str = Field(..., description="Name of the ECC agent to call (e.g., 'architect', 'code-reviewer')")
    prompt: str = Field(..., description="Prompt or instructions for the agent")
    context: Optional[str] = Field(default=None, description="Optional project or task context")


class CallECCAgentTool(BaseTool):
    name = "call_ecc_agent"
    description = "Invoke a specialized ECC agent with its full persona and instructions."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = CallECCAgentArgs

    def __init__(self, runner: Optional[ECCRunner] = None):
        super().__init__()
        self.runner = runner or ECC_RUNNER

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = CallECCAgentArgs(**arguments)
        res = await self.runner.call_agent(
            agent_name=args.agent_name,
            user_prompt=args.prompt,
            context=args.context,
        )
        return ToolResult(
            tool_name=self.name,
            success=res.success,
            output=res.output if res.success else (res.error or "Agent execution failed"),
            error=res.error,
            metadata={"agent": args.agent_name, "provider": res.provider, "model": res.model},
        )


class RunECCSkillArgs(BaseModel):
    skill_name: str = Field(..., description="Name of the ECC skill (e.g., 'accessibility', 'canvas-design')")
    script_name: Optional[str] = Field(default=None, description="Optional script to execute within the skill")
    args: List[str] = Field(default_factory=list, description="Arguments for the script")


class RunECCSkillTool(BaseTool):
    name = "run_ecc_skill"
    description = "Retrieve instructions or execute a script from a specialized ECC skill."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_2_WORKSPACE_REVERSIBLE
    args_schema = RunECCSkillArgs

    def __init__(self, runner: Optional[ECCRunner] = None):
        super().__init__()
        self.runner = runner or ECC_RUNNER

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = RunECCSkillArgs(**arguments)
        res = await self.runner.run_skill(
            skill_name=args.skill_name,
            script_name=args.script_name,
            args=args.args,
        )
        return ToolResult(
            tool_name=self.name,
            success=res.success,
            output=res.output if res.success else (res.error or "Skill execution failed"),
            error=res.error,
            metadata={"skill": args.skill_name, "is_script": res.is_script},
        )


class GetECCRulesArgs(BaseModel):
    rule_suite: str = Field(..., description="Language or framework name (e.g., 'python', 'typescript', 'react')")


class GetECCRulesTool(BaseTool):
    name = "get_ecc_rules"
    description = "Retrieve coding and architectural guidelines for a specific language or framework."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = GetECCRulesArgs

    def __init__(self, runner: Optional[ECCRunner] = None):
        super().__init__()
        self.runner = runner or ECC_RUNNER

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = GetECCRulesArgs(**arguments)
        rules = self.runner.get_rules(args.rule_suite)
        if rules:
            return ToolResult(
                tool_name=self.name,
                success=True,
                output="\n\n---\n\n".join(rules.values()),
                metadata={"rule_suite": args.rule_suite, "total_categories": len(rules)},
            )
        return ToolResult(
            tool_name=self.name,
            success=False,
            output="",
            error=f"No rule suite found for '{args.rule_suite}'.",
        )


class RunECCCommandArgs(BaseModel):
    command_name: str = Field(..., description="Name of the ECC command (e.g., 'git-commit', 'code-review')")
    input_args: Optional[str] = Field(default=None, description="Input arguments for the command")


class RunECCCommandTool(BaseTool):
    name = "run_ecc_command"
    description = "Execute a pre-configured ECC workflow command."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_2_WORKSPACE_REVERSIBLE
    args_schema = RunECCCommandArgs

    def __init__(self, runner: Optional[ECCRunner] = None):
        super().__init__()
        self.runner = runner or ECC_RUNNER

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = RunECCCommandArgs(**arguments)
        res = await self.runner.run_command(
            command_name=args.command_name,
            user_input=args.input_args or "",
        )
        return ToolResult(
            tool_name=self.name,
            success=res.success,
            output=res.output if res.success else (res.error or "Command execution failed"),
            error=res.error,
            metadata={"command": args.command_name},
        )


class SearchECCComponentsArgs(BaseModel):
    query: str = Field(..., description="Keywords to search for")
    component_type: Optional[str] = Field(
        default=None,
        description="Filter by 'agent', 'skill', 'rule', or 'command'. Omit for all.",
    )
    limit: int = Field(default=5, description="Max results per category")


class SearchECCComponentsTool(BaseTool):
    name = "search_ecc_components"
    description = "Search across 314 skills, 71 agents, 22 rule suites, and 98 commands."
    category = ToolCategory.CUSTOM
    permission_level = PermissionLevel.LEVEL_1_READ_ONLY
    args_schema = SearchECCComponentsArgs

    def __init__(self, registry: Optional[ECCRegistry] = None):
        super().__init__()
        self.registry = registry or ECC_REGISTRY

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        args = SearchECCComponentsArgs(**arguments)
        results: dict[str, Any] = {}

        ctype = (args.component_type or "").lower()
        if not ctype or ctype == "agent":
            agents = self.registry.search_agents(args.query, limit=args.limit)
            results["agents"] = [{"name": a.name, "description": a.description} for a in agents]

        if not ctype or ctype == "skill":
            skills = self.registry.search_skills(args.query, limit=args.limit)
            results["skills"] = [{"name": s.name, "description": s.description} for s in skills]

        if not ctype or ctype == "rule":
            suites = [s for s in self.registry.list_rule_suites() if args.query.lower() in s.name.lower()]
            results["rules"] = [{"name": s.name} for s in suites[:args.limit]]

        if not ctype or ctype == "command":
            commands = [c for c in self.registry.list_commands() if args.query.lower() in c.name.lower()]
            results["commands"] = [{"name": c.name, "description": c.description} for c in commands[:args.limit]]

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=str(results),
            metadata={"results_count": sum(len(v) for v in results.values())},
        )

