"""Pydantic data models for ECC components."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ECCAgent(BaseModel):
    """ECC Agent definition."""
    name: str
    description: str = ""
    tools: List[str] = Field(default_factory=list)
    model: str = "default"
    prompt: str = ""
    system_instructions: str = ""
    file_path: str = ""


class ECCSkill(BaseModel):
    """ECC Skill package definition."""
    name: str
    description: str = ""
    origin: str = "ECC"
    instructions: str = ""
    scripts: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    folder_path: str = ""


class ECCRuleSuite(BaseModel):
    """ECC Language or Framework Rule Suite."""
    name: str
    target_paths: List[str] = Field(default_factory=list)
    rules: Dict[str, str] = Field(default_factory=dict)  # category -> markdown content
    folder_path: str = ""


class ECCCommand(BaseModel):
    """ECC CLI or Slash Command definition."""
    name: str
    description: str = ""
    argument_hint: str = ""
    instructions: str = ""
    file_path: str = ""


class ECCWorkflow(BaseModel):
    """ECC Workflow pipeline definition."""
    name: str
    filename: str
    file_type: str  # js, json, md, etc.
    content: str = ""
    file_path: str = ""


class ComponentStats(BaseModel):
    """Summary statistics for all registered ECC components."""
    total_skills: int
    total_agents: int
    total_rule_suites: int
    total_commands: int
    total_workflows: int
    skills: List[str] = Field(default_factory=list)
    agents: List[str] = Field(default_factory=list)
    rule_suites: List[str] = Field(default_factory=list)
    commands: List[str] = Field(default_factory=list)
    workflows: List[str] = Field(default_factory=list)

