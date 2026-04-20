"""Prompt injection & input sanitiser for tool arguments."""

from __future__ import annotations

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Patterns that might indicate prompt injection in tool arguments
_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(previous|above|all)\s+(instructions?|prompts?)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"system\s*:?\s*override", re.IGNORECASE),
    re.compile(r"<\s*/?\s*(system|prompt|instruction)", re.IGNORECASE),
    re.compile(r"\{\{.*\}\}", re.IGNORECASE),  # template injection
    re.compile(r"```\s*(system|admin|root)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(a\s+)?(different|new)\s+(assistant|agent|ai)", re.IGNORECASE),
]

# Maximum length for any single string argument
_MAX_ARG_LENGTH = 5_000


class SanitisationError(Exception):
    """Raised when an input fails sanitisation checks."""
    pass


def sanitise_tool_input(tool_name: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and clean tool arguments.

    Raises SanitisationError if injection patterns are detected.
    """
    cleaned: dict[str, Any] = {}

    for key, value in kwargs.items():
        if isinstance(value, str):
            # Length check
            if len(value) > _MAX_ARG_LENGTH:
                raise SanitisationError(
                    f"Argument '{key}' for tool '{tool_name}' exceeds max length ({len(value)} > {_MAX_ARG_LENGTH})"
                )
            # Injection pattern check
            for pattern in _INJECTION_PATTERNS:
                if pattern.search(value):
                    logger.warning(
                        "Prompt injection detected",
                        extra={"tool": tool_name, "argument": key, "pattern": pattern.pattern},
                    )
                    raise SanitisationError(
                        f"Potential prompt injection detected in argument '{key}' for tool '{tool_name}'"
                    )
            # Strip control characters (except newlines/tabs)
            cleaned[key] = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
        elif isinstance(value, list):
            # Recursively sanitise lists of strings
            cleaned[key] = [
                sanitise_tool_input(tool_name, {"item": item})["item"]
                if isinstance(item, str) else item
                for item in value
            ]
        else:
            cleaned[key] = value

    return cleaned
