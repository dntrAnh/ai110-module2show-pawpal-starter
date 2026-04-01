"""
PawPal+ — Logic Layer
All backend classes for the pet care scheduling system.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
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
    # Recurrence: "none" | "daily" | "weekly"
    frequency: str = "none"
    # Scheduled start time as "HH:MM" string (24-hour); empty string = unscheduled
    start_time: str = ""
    # Next due date for recurring tasks; None means not yet set
    next_due: Optional[date] = field(default=None, compare=False)

    def complete(self) -> None:
        """Mark this task as completed and schedule the next occurrence for recurring tasks."""
        self.is_completed = True
        if self.frequency == "daily":
            self.next_due = date.today() + timedelta(days=1)
        elif self.frequency == "weekly":
            self.next_due = date.today() + timedelta(weeks=1)

    def spawn_next(self) -> Optional["Task"]:
        """Return a fresh, incomplete copy of this task due on next_due, or None if non-recurring."""
        if self.frequency == "none" or self.next_due is None:
            return None
        return Task(
            name=self.name,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            start_time=self.start_time,
            next_due=self.next_due,
        )

    def to_dict(self) -> dict:
        """Return a plain-dictionary representation of the task."""
        return {
            "name": self.name,
            "category": self.category,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "is_completed": self.is_completed,
            "frequency": self.frequency,
            "start_time": self.start_time,
            "next_due": self.next_due.isoformat() if self.next_due else None,
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
        unscheduled_tasks.  Completed recurring tasks automatically spawn their
        next occurrence back onto the pet's task list.
        """
        # Spawn next occurrences for any already-completed recurring tasks
        spawned: List[Task] = []
        for task in self.pet.get_tasks():
            if task.is_completed and task.frequency != "none":
                next_task = task.spawn_next()
                if next_task:
                    spawned.append(next_task)
        for t in spawned:
            self.pet.add_task(t)

        self.scheduled_tasks = []
        self.unscheduled_tasks = []
        remaining = self.time_budget_minutes
        sorted_tasks = sorted(
            [t for t in self.pet.get_tasks() if not t.is_completed],
            key=lambda t: t.priority,
        )
        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                self.scheduled_tasks.append(task)
                remaining -= task.duration_minutes
            else:
                self.unscheduled_tasks.append(task)
        return list(self.scheduled_tasks)

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Return tasks sorted ascending by start_time ("HH:MM"); unscheduled tasks go last.

        Uses a lambda key that converts "HH:MM" strings to comparable tuples so
        lexicographic ordering matches chronological ordering correctly.
        Tasks with no start_time set are placed at the end.
        """
        source = tasks if tasks is not None else self.scheduled_tasks

        def _time_key(t: Task):
            if t.start_time:
                h, m = t.start_time.split(":")
                return (0, int(h), int(m))
            return (1, 0, 0)   # no start_time → sort last

        return sorted(source, key=_time_key)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    @staticmethod
    def filter_tasks(
        tasks: List[Task],
        *,
        completed: Optional[bool] = None,
        category: Optional[str] = None,
        pet_name: Optional[str] = None,
        pet: Optional["Pet"] = None,
    ) -> List[Task]:
        """Return a filtered subset of *tasks* based on the supplied criteria.

        Args:
            tasks: Source list of Task objects to filter.
            completed: If True, keep only completed tasks; False keeps only pending.
                       None (default) keeps all regardless of status.
            category: If set, keep only tasks whose category matches (case-insensitive).
            pet_name: If set, keep only tasks belonging to the named pet (requires
                      tasks to carry a pet reference — use alongside *pet* parameter).
            pet: If provided, filter tasks to only those present in pet.tasks.
        """
        result = tasks
        if completed is not None:
            result = [t for t in result if t.is_completed == completed]
        if category is not None:
            result = [t for t in result if t.category.lower() == category.lower()]
        if pet is not None:
            pet_task_ids = {id(t) for t in pet.tasks}
            result = [t for t in result if id(t) in pet_task_ids]
        return result

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> List[str]:
        """Scan scheduled_tasks for overlapping time windows and return warning strings.

        A conflict occurs when two tasks share the same start_time, or when one
        task's time window (start_time + duration) overlaps another's.
        Tasks without a start_time are skipped (they cannot conflict on time).
        Returns a list of warning message strings; empty list means no conflicts.
        """
        warnings: List[str] = []
        timed = [t for t in self.scheduled_tasks if t.start_time]

        def _to_minutes(hhmm: str) -> int:
            """Convert 'HH:MM' to total minutes since midnight."""
            h, m = hhmm.split(":")
            return int(h) * 60 + int(m)

        for i, a in enumerate(timed):
            a_start = _to_minutes(a.start_time)
            a_end = a_start + a.duration_minutes
            for b in timed[i + 1:]:
                b_start = _to_minutes(b.start_time)
                b_end = b_start + b.duration_minutes
                # Overlap when one window starts before the other ends
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"⚠️  Conflict: '{a.name}' ({a.start_time}–{a_end // 60:02d}:{a_end % 60:02d}) "
                        f"overlaps '{b.name}' ({b.start_time}–{b_end // 60:02d}:{b_end % 60:02d})"
                    )
        return warnings

    # ------------------------------------------------------------------
    # Next available slot
    # ------------------------------------------------------------------

    def find_next_slot(
        self,
        duration_minutes: int,
        search_from: str = "07:00",
        end_by: str = "22:00",
    ) -> Optional[str]:
        """Find the earliest free time window that fits *duration_minutes*.

        The algorithm builds a sorted list of occupied intervals from every
        timed task in *scheduled_tasks*, then walks candidate start times in
        1-minute steps from *search_from* until it finds a window of the
        requested length that does not overlap any occupied interval, or until
        *end_by* is reached.

        Args:
            duration_minutes: Length of the window to find, in minutes.
            search_from: Earliest candidate start time in ``"HH:MM"`` format.
                         Defaults to ``"07:00"``.
            end_by: Latest time by which the window must *end*, in ``"HH:MM"``
                    format.  Defaults to ``"22:00"``.

        Returns:
            The first available ``"HH:MM"`` start time as a string, or
            ``None`` if no slot exists within the requested window.

        Raises:
            ValueError: If *duration_minutes* is less than 1, or if
                        *search_from* / *end_by* are not valid ``"HH:MM"``
                        strings.
        """
        if duration_minutes < 1:
            raise ValueError("duration_minutes must be at least 1.")

        def _mins(hhmm: str) -> int:
            parts = hhmm.split(":")
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                raise ValueError(f"Invalid time string: {hhmm!r}. Expected 'HH:MM'.")
            return int(parts[0]) * 60 + int(parts[1])

        start_bound = _mins(search_from)
        end_bound   = _mins(end_by)

        if start_bound + duration_minutes > end_bound:
            return None

        # Build sorted list of (start, end) occupied intervals from timed tasks
        occupied: List[tuple] = sorted(
            (_mins(t.start_time), _mins(t.start_time) + t.duration_minutes)
            for t in self.scheduled_tasks
            if t.start_time
        )

        candidate = start_bound
        while candidate + duration_minutes <= end_bound:
            candidate_end = candidate + duration_minutes
            # Check if this candidate window overlaps any occupied interval
            conflict = any(
                candidate < occ_end and occ_start < candidate_end
                for occ_start, occ_end in occupied
            )
            if not conflict:
                return f"{candidate // 60:02d}:{candidate % 60:02d}"
            # Jump to the end of the first overlapping interval to skip ahead
            for occ_start, occ_end in occupied:
                if candidate < occ_end and occ_start < candidate_end:
                    candidate = occ_end
                    break
            else:
                candidate += 1  # safety increment (should not normally be reached)

        return None  # no free slot found within the window

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
