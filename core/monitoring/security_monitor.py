"""Security Monitor for Payal AI.

Monitors real-time agent, tool, and system activities for unauthorized privilege escalation,
sensitive credential exposure, dangerous commands, and directory traversal.
"""

from dataclasses import dataclass, field
import re
import time
from typing import Any, Dict, List, Optional


@dataclass
class SecurityIncident:
    incident_id: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    action: str
    target: str
    description: str
    timestamp: float
    blocked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecurityMonitor:
    """Monitors tool calls, arguments, and system tasks for safety guardrails."""

    DANGEROUS_PATTERNS = [
        (r"(rm\s+-rf\s+[\/~]|\bformat\s+[c-z]:|\b(del|rmdir|remove-item)\b.*system32|system32)", "CRITICAL", "Destructive system deletion detected"),
        (r"(\.env|id_rsa|id_ed25519|\.aws\/credentials|\.ssh\/|\/etc\/shadow)", "HIGH", "Sensitive credential access attempted"),
        (r"(\.\.[\/\\]\.\.[\/\\]\.\.)", "MEDIUM", "Severe directory traversal attempt detected"),
        (r"(chmod\s+777|takeown|icacls.*grant.*everyone)", "MEDIUM", "Broad permission escalation attempt"),
        (r"(Invoke-Expression|IEX\s*\(|curl.*\|\s*sh|curl.*\|\s*bash)", "HIGH", "Unchecked remote payload execution attempted"),
    ]

    def __init__(self):
        self._incidents: List[SecurityIncident] = []
        self._counter: int = 0

    def evaluate_action(
        self,
        action: str,
        target: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Inspect an action before execution. Returns whether it is permitted or blocked."""
        args_str = str(arguments or {})
        combined_payload = f"{action} {target} {args_str}"

        for pattern, severity, desc in self.DANGEROUS_PATTERNS:
            if re.search(pattern, combined_payload, re.IGNORECASE):
                self._counter += 1
                incident_id = f"sec-{int(time.time())}-{self._counter}"
                is_blocked = severity in ["HIGH", "CRITICAL"]

                incident = SecurityIncident(
                    incident_id=incident_id,
                    severity=severity,
                    action=action,
                    target=target,
                    description=desc,
                    timestamp=time.time(),
                    blocked=is_blocked,
                    metadata={"pattern": pattern, "args": args_str[:200]},
                )
                self._incidents.append(incident)

                return {
                    "allowed": not is_blocked,
                    "blocked": is_blocked,
                    "severity": severity,
                    "reason": desc,
                    "incident_id": incident_id,
                }

        return {
            "allowed": True,
            "blocked": False,
            "severity": "SAFE",
            "reason": "Security checks passed",
            "incident_id": None,
        }

    def get_incidents(
        self,
        limit: int = 50,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return recorded security incidents."""
        incidents = self._incidents
        if severity:
            incidents = [i for i in incidents if i.severity == severity.upper()]
        recent = incidents[-limit:]
        return [
            {
                "incident_id": i.incident_id,
                "severity": i.severity,
                "action": i.action,
                "target": i.target,
                "description": i.description,
                "timestamp": i.timestamp,
                "blocked": i.blocked,
                "metadata": i.metadata,
            }
            for i in reversed(recent)
        ]

    def clear_incidents(self) -> None:
        self._incidents.clear()


SECURITY_MONITOR = SecurityMonitor()
