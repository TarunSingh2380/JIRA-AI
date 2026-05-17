"""Shared graph job data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphJob:
    id: str
    action: str
    status: str
    created_at: str
    updated_at: str
    options: dict[str, Any]
    totals: dict[str, int] = field(default_factory=dict)
    progress: dict[str, int] = field(default_factory=dict)
    repositories: list[dict[str, Any]] = field(default_factory=list)
    jira_tickets: list[dict[str, Any]] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
