"""Component Selector for Payal Unified Orchestrator.

Analyzes user goals and tasks to dynamically select the most relevant
ECC Agents, Skills, Rule Suites, and Commands from the catalog.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional

from integrations.ecc.models import ECCAgent, ECCCommand, ECCRuleSuite, ECCSkill
from integrations.ecc.registry import ECC_REGISTRY, ECCRegistry


@dataclass
class ComponentSelection:
    """Selected components matched to a user goal."""
    goal: str
    primary_agent: Optional[ECCAgent] = None
    supporting_agents: List[ECCAgent] = field(default_factory=list)
    recommended_skills: List[ECCSkill] = field(default_factory=list)
    applicable_rules: List[ECCRuleSuite] = field(default_factory=list)
    relevant_commands: List[ECCCommand] = field(default_factory=list)
    confidence_score: float = 0.8
    intent_tags: List[str] = field(default_factory=list)


class ComponentSelector:
    """Matches user goals and keywords against loaded ECC components."""

    # Domain keywords mapped to primary agents and skills
    DOMAIN_PATTERNS = {
        "frontend": {
            "keywords": ["ui", "frontend", "react", "vue", "css", "html", "web", "tailwind", "design", "component", "button", "layout"],
            "agent_candidates": ["react-reviewer", "react-build-resolver", "vue-reviewer", "type-design-analyzer", "a11y-architect", "code-architect", "architect"],
            "skill_candidates": ["frontend-design-direction", "design-system", "react-patterns", "react-performance", "dashboard-builder"],
            "rule_candidates": ["react", "typescript", "javascript", "css"],
        },
        "backend": {
            "keywords": ["api", "backend", "fastapi", "database", "sql", "server", "endpoint", "rest", "microservice", "auth", "token"],
            "agent_candidates": ["fastapi-reviewer", "database-reviewer", "django-reviewer", "django-build-resolver", "code-architect", "architect"],
            "skill_candidates": ["bigquery-sql", "cloud-databases-onboarding"],
            "rule_candidates": ["python", "go", "rust", "sql", "nodejs"],
        },
        "security": {
            "keywords": ["security", "pentest", "vulnerability", "exploit", "kali", "audit", "compliance", "threat", "auth", "owasp", "cert"],
            "agent_candidates": ["security-reviewer", "silent-failure-hunter", "refactor-cleaner", "code-architect"],
            "skill_candidates": ["harness-engineering"],
            "rule_candidates": ["security"],
        },
        "devops": {
            "keywords": ["devops", "ci", "cd", "docker", "kubernetes", "cloud", "deploy", "pipeline", "sre", "git", "infrastructure"],
            "agent_candidates": ["build-error-resolver", "e2e-runner", "harness-optimizer", "network-architect"],
            "skill_candidates": ["harness-engineering"],
            "rule_candidates": ["docker", "kubernetes", "bash"],
        },
        "science": {
            "keywords": ["biology", "chemistry", "physics", "genomics", "rna", "protein", "math", "simulation", "ml", "data", "stats"],
            "agent_candidates": ["mle-reviewer", "pytorch-build-resolver", "gan-generator", "gan-evaluator", "gan-planner"],
            "skill_candidates": ["biopython", "rdkit", "polars", "scikit-learn", "sympy", "pysam", "anndata"],
            "rule_candidates": ["python"],
        },
        "review": {
            "keywords": ["review", "audit", "refactor", "clean", "lint", "inspect", "test", "coverage", "verify", "benchmark"],
            "agent_candidates": ["code-reviewer", "code-simplifier", "refactor-cleaner", "comment-analyzer", "commit-reviewer"],
            "skill_candidates": ["ponytail", "ponytail-audit", "ponytail-review"],
            "rule_candidates": ["python", "typescript"],
        },
    }

    def __init__(self, registry: Optional[ECCRegistry] = None):
        self.registry = registry or ECC_REGISTRY

    def select(self, goal: str, context: Optional[str] = None) -> ComponentSelection:
        """Select matching agents, skills, rules, and commands for the goal."""
        text = f"{goal} {context or ''}".lower()
        words = set(re.findall(r"\b\w+\b", text))

        matched_domains: List[str] = []
        candidate_agents: List[str] = []
        candidate_skills: List[str] = []
        candidate_rules: List[str] = []

        # 1. Match against domain patterns with overlap ranking
        domain_matches = []
        for domain, spec in self.DOMAIN_PATTERNS.items():
            overlap = words.intersection(spec["keywords"])
            if overlap:
                domain_matches.append((len(overlap), domain, spec))

        # Sort domains by number of matching keywords descending
        domain_matches.sort(key=lambda x: x[0], reverse=True)

        for _, domain, spec in domain_matches:
            matched_domains.append(domain)
            candidate_agents.extend(spec["agent_candidates"])
            candidate_skills.extend(spec["skill_candidates"])
            candidate_rules.extend(spec["rule_candidates"])

        # 2. Direct registry search to capture niche agents & skills
        direct_agents = self.registry.search_agents(goal, limit=5)
        for da in direct_agents:
            if da.name not in candidate_agents:
                candidate_agents.append(da.name)

        direct_skills = self.registry.search_skills(goal, limit=6)
        for ds in direct_skills:
            if ds.name not in candidate_skills:
                candidate_skills.append(ds.name)

        # Fallback primary agent if none matched
        if not candidate_agents:
            candidate_agents = ["code-architect", "code-reviewer"]

        # Resolve objects from registry
        resolved_agents: List[ECCAgent] = []
        for name in candidate_agents:
            agent = self.registry.get_agent(name)
            if agent and agent not in resolved_agents:
                resolved_agents.append(agent)

        primary_agent = resolved_agents[0] if resolved_agents else None
        supporting_agents = resolved_agents[1:4] if len(resolved_agents) > 1 else []

        resolved_skills: List[ECCSkill] = []
        for name in candidate_skills:
            skill = self.registry.get_skill(name)
            if skill and skill not in resolved_skills:
                resolved_skills.append(skill)

        resolved_rules: List[ECCRuleSuite] = []
        for name in candidate_rules:
            rule = self.registry.get_rule_suite(name)
            if rule and rule not in resolved_rules:
                resolved_rules.append(rule)

        # Find relevant commands (e.g., git, review, build)
        relevant_commands: List[ECCCommand] = []
        for cmd in self.registry.list_commands():
            cmd_words = set(re.findall(r"\b\w+\b", f"{cmd.name} {cmd.description}".lower()))
            if words.intersection(cmd_words):
                relevant_commands.append(cmd)
                if len(relevant_commands) >= 3:
                    break

        confidence = 0.9 if matched_domains else 0.7

        return ComponentSelection(
            goal=goal,
            primary_agent=primary_agent,
            supporting_agents=supporting_agents,
            recommended_skills=resolved_skills[:6],
            applicable_rules=resolved_rules[:4],
            relevant_commands=relevant_commands,
            confidence_score=confidence,
            intent_tags=matched_domains,
        )


# Global singleton component selector
COMPONENT_SELECTOR = ComponentSelector()

