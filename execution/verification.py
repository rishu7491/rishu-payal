"""Verification & Recovery Engine for Payal Core Engine.

Verifies step outputs, detects errors and silent failures, and orchestrates
automated recovery attempts before escalating to the user.
"""

import ast
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class VerificationResult:
    """Outcome of a verification check."""
    success: bool
    message: str
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    recovery_suggested: bool = False
    recovery_strategy: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class VerificationEngine:
    """Inspects execution outputs against quality contracts and triggers recovery."""

    # Common failure patterns
    ERROR_INDICATORS = [
        "Traceback (most recent call last):",
        "SyntaxError:",
        "TypeError:",
        "ValueError:",
        "ImportError:",
        "ModuleNotFoundError:",
        "AssertionError:",
        "FAILED (failures=",
        "FATAL:",
        "Panic:",
    ]

    def verify_python_code(self, code_str: str) -> VerificationResult:
        """Validate that generated Python code parses into valid AST without syntax errors."""
        try:
            ast.parse(code_str)
            return VerificationResult(
                success=True,
                message="Python code AST verified successfully.",
                passed_checks=["AST_PARSER"],
            )
        except SyntaxError as e:
            return VerificationResult(
                success=False,
                message=f"Syntax error at line {e.lineno}: {e.msg}",
                failed_checks=["AST_PARSER"],
                recovery_suggested=True,
                recovery_strategy="syntax_repair",
                diagnostics={"line": e.lineno, "offset": e.offset, "text": e.text},
            )

    def verify_command_output(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        expected_patterns: Optional[List[str]] = None,
    ) -> VerificationResult:
        """Verify command line execution output."""
        passed = []
        failed = []

        # Check exit code
        if exit_code == 0:
            passed.append("EXIT_CODE_ZERO")
        else:
            failed.append("EXIT_CODE_NON_ZERO")

        # Check for error indicators in stderr and stdout
        combined_output = f"{stdout}\n{stderr}"
        found_errors = [err for err in self.ERROR_INDICATORS if err in combined_output]
        if not found_errors:
            passed.append("NO_ERROR_PATTERNS")
        else:
            failed.append("DETECTED_ERROR_PATTERNS")

        # Check expected output patterns
        if expected_patterns:
            for pat in expected_patterns:
                if pat in combined_output:
                    passed.append(f"PATTERN_{pat}")
                else:
                    failed.append(f"MISSING_PATTERN_{pat}")

        success = exit_code == 0 and len(found_errors) == 0 and (not expected_patterns or not any(f.startswith("MISSING") for f in failed))
        recovery_strategy = None
        if not success:
            if "ModuleNotFoundError" in combined_output or "ImportError" in combined_output:
                recovery_strategy = "dependency_install"
            elif "SyntaxError" in combined_output:
                recovery_strategy = "syntax_repair"
            else:
                recovery_strategy = "agent_review_and_retry"

        return VerificationResult(
            success=success,
            message="Verification passed." if success else f"Verification failed on: {', '.join(failed)}",
            passed_checks=passed,
            failed_checks=failed,
            recovery_suggested=not success,
            recovery_strategy=recovery_strategy,
            diagnostics={"found_errors": found_errors, "exit_code": exit_code},
        )

    def verify_agent_output(self, output: str, min_length: int = 10) -> VerificationResult:
        """Verify that an agent produced a coherent, non-empty response."""
        clean_text = output.strip()
        if len(clean_text) < min_length:
            return VerificationResult(
                success=False,
                message=f"Agent response is too short ({len(clean_text)} chars).",
                failed_checks=["MIN_LENGTH"],
                recovery_suggested=True,
                recovery_strategy="retry_agent_with_expanded_prompt",
            )

        return VerificationResult(
            success=True,
            message="Agent output verified.",
            passed_checks=["NON_EMPTY", "MIN_LENGTH"],
        )


# Global singleton verification engine
VERIFICATION_ENGINE = VerificationEngine()

