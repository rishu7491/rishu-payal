"""Central in-memory registry for all loaded ECC components."""

from typing import Dict, List, Optional
from .loader import ECCLoader
from .models import (
    ComponentStats,
    ECCAgent,
    ECCCommand,
    ECCRuleSuite,
    ECCSkill,
    ECCWorkflow,
)


class ECCRegistry:
    """Indexed catalog providing fast lookups and semantic filtering."""

    def __init__(self, loader: Optional[ECCLoader] = None, auto_load: bool = True):
        self.loader = loader or ECCLoader()
        self.skills: Dict[str, ECCSkill] = {}
        self.agents: Dict[str, ECCAgent] = {}
        self.rule_suites: Dict[str, ECCRuleSuite] = {}
        self.commands: Dict[str, ECCCommand] = {}
        self.workflows: Dict[str, ECCWorkflow] = {}

        if auto_load:
            self.load()

    def load(self) -> None:
        """Load all ECC components from disk."""
        self.agents = self.loader.load_agents()
        self.skills = self.loader.load_skills()
        self.rule_suites = self.loader.load_rule_suites()
        self.commands = self.loader.load_commands()
        self.workflows = self.loader.load_workflows()

    def get_agent(self, name: str) -> Optional[ECCAgent]:
        """Retrieve an agent by name."""
        return self.agents.get(name)

    def get_skill(self, name: str) -> Optional[ECCSkill]:
        """Retrieve a skill by name."""
        return self.skills.get(name)

    def get_rule_suite(self, name: str) -> Optional[ECCRuleSuite]:
        """Retrieve a rule suite by language/technology name."""
        return self.rule_suites.get(name)

    def get_command(self, name: str) -> Optional[ECCCommand]:
        """Retrieve a command by name."""
        return self.commands.get(name)

    def get_workflow(self, name: str) -> Optional[ECCWorkflow]:
        """Retrieve a workflow by name."""
        return self.workflows.get(name)

    def list_agents(self) -> List[ECCAgent]:
        return list(self.agents.values())

    def list_skills(self) -> List[ECCSkill]:
        return list(self.skills.values())

    def list_rule_suites(self) -> List[ECCRuleSuite]:
        return list(self.rule_suites.values())

    def list_commands(self) -> List[ECCCommand]:
        return list(self.commands.values())

    def list_workflows(self) -> List[ECCWorkflow]:
        return list(self.workflows.values())

    def search_agents(self, query: str, limit: int = 5) -> List[ECCAgent]:
        """Search agents by name or description keywords."""
        import re
        q = query.lower()
        terms = [t for t in re.findall(r"\b\w+\b", q) if len(t) > 2 and t not in ["with", "from", "that", "this", "your", "have"]]
        scored: List[tuple[int, ECCAgent]] = []
        for agent in self.agents.values():
            score = 0
            name_lower = agent.name.lower()
            desc_lower = agent.description.lower()
            if q in name_lower:
                score += 20
            for term in terms:
                if term in name_lower:
                    score += 8
                if term in desc_lower:
                    score += 2
            if score > 0:
                scored.append((score, agent))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:limit]]

    def search_skills(self, query: str, limit: int = 10) -> List[ECCSkill]:
        """Search skills by name or description keywords."""
        import re
        q = query.lower()
        terms = [t for t in re.findall(r"\b\w+\b", q) if len(t) > 2 and t not in ["with", "from", "that", "this", "your", "have"]]
        scored: List[tuple[int, ECCSkill]] = []
        for skill in self.skills.values():
            score = 0
            name_lower = skill.name.lower()
            desc_lower = skill.description.lower()
            if q in name_lower:
                score += 20
            for term in terms:
                if term in name_lower:
                    score += 8
                if term in desc_lower:
                    score += 2
            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]

    def get_stats(self) -> ComponentStats:
        """Return counts and keys of all registered components."""
        return ComponentStats(
            total_skills=len(self.skills),
            total_agents=len(self.agents),
            total_rule_suites=len(self.rule_suites),
            total_commands=len(self.commands),
            total_workflows=len(self.workflows),
            skills=sorted(list(self.skills.keys())),
            agents=sorted(list(self.agents.keys())),
            rule_suites=sorted(list(self.rule_suites.keys())),
            commands=sorted(list(self.commands.keys())),
            workflows=sorted(list(self.workflows.keys())),
        )


# Global singleton instance
ECC_REGISTRY = ECCRegistry(auto_load=True)

