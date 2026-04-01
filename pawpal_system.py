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
        self.is_completed = True

    def to_dict(self) -> dict:
        """Return a plain-dictionary representation of the task."""
        return {
            "name": self.name,
            "category": self.category,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "is_completed": self.is_completed,
        }


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
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove a task by name from this pet's task list."""
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def get_tasks(self) -> List[Task]:
        """Return all tasks assigned to this pet."""
        return list(self.tasks)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner and their daily time budget."""

    def __init__(self, name: str, available_time_minutes: int) -> None:
        """Initialize an owner with a name and their total daily care time in minutes."""
        self.name: str = name
        self.available_time_minutes: int = available_time_minutes
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner and back-link it."""
        pet.owner = self
        self.pets.append(pet)

    def get_available_time(self) -> int:
        """Return the owner's total daily time budget in minutes."""
        return self.available_time_minutes

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]


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
        """Set up the scheduler for *pet*, using the supplied budget or the owner's budget."""
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
        Sort tasks by priority (lower number = higher priority), fit as many as
        possible within the time budget, and populate scheduled_tasks and
        unscheduled_tasks.
        """
        self.scheduled_tasks = []
        self.unscheduled_tasks = []
        remaining = self.time_budget_minutes
        sorted_tasks = sorted(self.pet.get_tasks(), key=lambda t: t.priority)
        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                self.scheduled_tasks.append(task)
                remaining -= task.duration_minutes
            else:
                self.unscheduled_tasks.append(task)
        return list(self.scheduled_tasks)

    def explain_plan(self) -> str:
        """
        Return a human-readable explanation of why each task was included
        or excluded from the generated schedule.
        """
        if not self.scheduled_tasks and not self.unscheduled_tasks:
            return "No schedule generated yet. Call generate_schedule() first."

        lines: List[str] = []
        total = sum(t.duration_minutes for t in self.scheduled_tasks)
        lines.append(
            f"Time budget: {self.time_budget_minutes} min  |  "
            f"Used: {total} min  |  "
            f"Remaining: {self.time_budget_minutes - total} min"
        )
        lines.append("")
        lines.append("Scheduled tasks:")
        for task in self.scheduled_tasks:
            lines.append(
                f"  ✓ [{task.priority}] {task.name} ({task.category}) — {task.duration_minutes} min"
            )
        if self.unscheduled_tasks:
            lines.append("")
            lines.append("Skipped (not enough time):")
            for task in self.unscheduled_tasks:
                lines.append(
                    f"  ✗ [{task.priority}] {task.name} ({task.category}) — {task.duration_minutes} min"
                )
        return "\n".join(lines)


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
        """Initialize an empty diagram with an optional title."""
        self.title: str = title
        self.classes: List[dict] = []
        self.relationships: List[str] = []
        self.diagram_text: str = ""

    def add_class(self, cls: dict) -> None:
        """
        Add a class definition dict to the diagram.
        Expected keys: 'name', 'attributes' (list of str), 'methods' (list of str).
        """
        self.classes.append(cls)

    def add_relationship(self, rel: str) -> None:
        """Add a relationship line (raw Mermaid syntax) to the diagram."""
        self.relationships.append(rel)

    def render(self) -> str:
        """Compile all classes and relationships into a Mermaid classDiagram string."""
        lines = ["classDiagram"]
        for cls in self.classes:
            lines.append(f"    class {cls['name']} {{")
            for attr in cls.get("attributes", []):
                lines.append(f"        {attr}")
            for method in cls.get("methods", []):
                lines.append(f"        {method}")
            lines.append("    }")
            lines.append("")
        for rel in self.relationships:
            lines.append(f"    {rel}")
        self.diagram_text = "\n".join(lines)
        return self.diagram_text

    def export(self, filepath: str) -> None:
        """Write the rendered diagram wrapped in a Markdown code-fence to a file."""
        content = f"```mermaid\n{self.render()}\n```\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
