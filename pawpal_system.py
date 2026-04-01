"""
PawPal+ — Logic Layer
All backend classes for the pet care scheduling system.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care activity."""

    name: str
    category: str          # e.g. "walk", "feeding", "medication", "grooming"
    duration_minutes: int
    priority: int          # 1 = highest priority
    is_completed: bool = False

    def complete(self) -> None:
        """Mark this task as completed."""
        pass  # TODO: implement

    def to_dict(self) -> dict:
        """Return a plain-dictionary representation of the task."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet owned by an Owner."""

    name: str
    species: str           # e.g. "dog", "cat", "other"
    age: int
    owner: Optional["Owner"] = field(default=None, repr=False)
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's task list."""
        pass  # TODO: implement

    def remove_task(self, task_name: str) -> None:
        """Remove a task by name from this pet's task list."""
        pass  # TODO: implement

    def get_tasks(self) -> List[Task]:
        """Return all tasks assigned to this pet."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner and their daily time budget."""

    def __init__(self, name: str, available_time_minutes: int) -> None:
        self.name: str = name
        self.available_time_minutes: int = available_time_minutes
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner and back-link it."""
        pass  # TODO: implement

    def get_available_time(self) -> int:
        """Return the owner's total daily time budget in minutes."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Generates a prioritized daily care plan for a pet.

    Tasks are selected by priority until the owner's time budget is exhausted.
    Tasks that do not fit are collected in unscheduled_tasks.
    """

    def __init__(self, pet: Pet, time_budget_minutes: Optional[int] = None) -> None:
        self.pet: Pet = pet
        # Prefer the explicitly supplied budget; fall back to the owner's budget.
        if time_budget_minutes is not None:
            self.time_budget_minutes: int = time_budget_minutes
        elif pet.owner is not None:
            self.time_budget_minutes = pet.owner.available_time_minutes
        else:
            self.time_budget_minutes = 0
        self.scheduled_tasks: List[Task] = []
        self.unscheduled_tasks: List[Task] = []

    def generate_schedule(self) -> List[Task]:
        """
        Sort tasks by priority, fit as many as possible within the time budget,
        and return the scheduled list.
        """
        pass  # TODO: implement

    def explain_plan(self) -> str:
        """
        Return a human-readable explanation of why each task was included
        or excluded from the generated schedule.
        """
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# MermaidDiagram
# ---------------------------------------------------------------------------

class MermaidDiagram:
    """
    Builds and renders a Mermaid.js class diagram as a text string.

    Usage:
        diagram = MermaidDiagram(title="PawPal+ System")
        diagram.add_class({"name": "Owner", "attributes": [...], "methods": [...]})
        diagram.add_relationship("Owner '1' --> '1..*' Pet : owns")
        print(diagram.render())
        diagram.export("diagram.md")
    """

    def __init__(self, title: str = "") -> None:
        self.title: str = title
        self.classes: List[dict] = []
        self.relationships: List[str] = []
        self.diagram_text: str = ""

    def add_class(self, cls: dict) -> None:
        """
        Add a class definition dict to the diagram.
        Expected keys: 'name', 'attributes' (list of str), 'methods' (list of str).
        """
        pass  # TODO: implement

    def add_relationship(self, rel: str) -> None:
        """Add a relationship line (raw Mermaid syntax) to the diagram."""
        pass  # TODO: implement

    def render(self) -> str:
        """Compile all classes and relationships into a Mermaid classDiagram string."""
        pass  # TODO: implement

    def export(self, filepath: str) -> None:
        """Write the rendered diagram wrapped in a Markdown code-fence to a file."""
        pass  # TODO: implement
