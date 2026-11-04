"""ECC Component Loader.

Discovers and parses all 314 Skills, 71 Agents, 22 Rule Suites,
and 98 Commands/Workflows without modifying any original files.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

from .models import (
    ECCAgent,
    ECCCommand,
    ECCRuleSuite,
    ECCSkill,
    ECCWorkflow,
)


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter delimited by '---' from markdown content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
                if isinstance(meta, dict):
                    return meta, parts[2].strip()
            except Exception:
                pass
    return {}, content.strip()


class ECCLoader:
    """Discovers, parses, and loads ECC components into memory."""

    def __init__(self, payal_root: Optional[Path] = None):
        if payal_root is None:
            # payal/integrations/ecc/loader.py -> payal root is 2 levels up
            self.root = Path(__file__).resolve().parents[2]
        else:
            self.root = Path(payal_root)

        self.skills_dir = self.root / "skills"
        self.agents_dir = self.root / "agents" / "ecc"
        self.rules_dir = self.root / "rules"
        self.commands_dir = self.root / "commands"
        self.workflows_dir = self.root / "workflows"

    def load_agents(self) -> Dict[str, ECCAgent]:
        """Load all 71 agent definitions from payal/agents/ecc."""
        agents: Dict[str, ECCAgent] = {}
        if not self.agents_dir.exists():
            return agents

        for entry in self.agents_dir.glob("*.md"):
            try:
                content = entry.read_text(encoding="utf-8", errors="ignore")
                meta, body = parse_frontmatter(content)
                name = meta.get("name") or entry.stem
                description = meta.get("description", "")
                tools_raw = meta.get("tools", [])
                if isinstance(tools_raw, str):
                    tools = [t.strip() for t in tools_raw.split(",") if t.strip()]
                elif isinstance(tools_raw, list):
                    tools = [str(t).strip() for t in tools_raw if str(t).strip()]
                else:
                    tools = []

                model = str(meta.get("model", "default"))

                agents[name] = ECCAgent(
                    name=name,
                    description=description,
                    tools=tools,
                    model=model,
                    prompt=body,
                    system_instructions=body,
                    file_path=str(entry),
                )
            except Exception:
                continue

        return agents

    def load_skills(self) -> Dict[str, ECCSkill]:
        """Load all 314 skills from payal/skills/."""
        skills: Dict[str, ECCSkill] = {}
        if not self.skills_dir.exists():
            return skills

        for folder in self.skills_dir.iterdir():
            if not folder.is_dir():
                continue

            skill_md = folder / "SKILL.md"
            if not skill_md.is_file():
                continue

            try:
                content = skill_md.read_text(encoding="utf-8", errors="ignore")
                meta, body = parse_frontmatter(content)
                name = meta.get("name") or folder.name
                description = meta.get("description", "")
                origin = meta.get("metadata", {}).get("origin", "ECC") if isinstance(meta.get("metadata"), dict) else "ECC"

                scripts = []
                scripts_dir = folder / "scripts"
                if scripts_dir.is_dir():
                    scripts = [str(p.name) for p in scripts_dir.iterdir() if p.is_file()]

                references = []
                ref_dir = folder / "references"
                if ref_dir.is_dir():
                    references = [str(p.name) for p in ref_dir.iterdir() if p.is_file()]

                skills[name] = ECCSkill(
                    name=name,
                    description=description,
                    origin=origin,
                    instructions=body,
                    scripts=scripts,
                    references=references,
                    folder_path=str(folder),
                )
            except Exception:
                continue

        return skills

    def load_rule_suites(self) -> Dict[str, ECCRuleSuite]:
        """Load all 22 rule suites from payal/rules/."""
        rule_suites: Dict[str, ECCRuleSuite] = {}
        if not self.rules_dir.exists():
            return rule_suites

        for folder in self.rules_dir.iterdir():
            if not folder.is_dir():
                continue

            suite_name = folder.name
            target_paths: List[str] = []
            rules_dict: Dict[str, str] = {}

            for md_file in folder.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8", errors="ignore")
                    meta, body = parse_frontmatter(content)
                    category = md_file.stem  # e.g., coding-style, security, patterns
                    rules_dict[category] = body

                    paths_meta = meta.get("paths", [])
                    if isinstance(paths_meta, list):
                        target_paths.extend([str(p) for p in paths_meta])
                except Exception:
                    continue

            rule_suites[suite_name] = ECCRuleSuite(
                name=suite_name,
                target_paths=list(set(target_paths)),
                rules=rules_dict,
                folder_path=str(folder),
            )

        return rule_suites

    def load_commands(self) -> Dict[str, ECCCommand]:
        """Load all 98 commands from payal/commands/."""
        commands: Dict[str, ECCCommand] = {}
        if not self.commands_dir.exists():
            return commands

        for cmd_file in self.commands_dir.glob("*.md"):
            try:
                content = cmd_file.read_text(encoding="utf-8", errors="ignore")
                meta, body = parse_frontmatter(content)
                name = cmd_file.stem
                description = meta.get("description", "")
                arg_hint = meta.get("argument-hint", "")

                commands[name] = ECCCommand(
                    name=name,
                    description=description,
                    argument_hint=arg_hint,
                    instructions=body,
                    file_path=str(cmd_file),
                )
            except Exception:
                continue

        return commands

    def load_workflows(self) -> Dict[str, ECCWorkflow]:
        """Load workflows from payal/workflows/."""
        workflows: Dict[str, ECCWorkflow] = {}
        if not self.workflows_dir.exists():
            return workflows

        for wf_file in self.workflows_dir.iterdir():
            if not wf_file.is_file():
                continue
            try:
                name = wf_file.stem
                ext = wf_file.suffix.lstrip(".")
                content = wf_file.read_text(encoding="utf-8", errors="ignore")

                workflows[name] = ECCWorkflow(
                    name=name,
                    filename=wf_file.name,
                    file_type=ext,
                    content=content,
                    file_path=str(wf_file),
                )
            except Exception:
                continue

        return workflows

