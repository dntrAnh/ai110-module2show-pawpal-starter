"""
Unit tests for PawPal+ core logic.
Run with:  python -m pytest
"""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_task() -> Task:
    """Return a fresh, incomplete task for use in tests."""
    return Task(name="Morning walk", category="walk", duration_minutes=30, priority=1)


@pytest.fixture
def sample_pet() -> Pet:
    """Return a pet with no tasks attached."""
    return Pet(name="Mochi", species="dog", age=3)


@pytest.fixture
def owner_with_pet(sample_pet: Pet) -> Owner:
    """Return an owner who already has one pet registered."""
    owner = Owner(name="Jordan", available_time_minutes=90)
    owner.add_pet(sample_pet)
    return owner


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

class TestTask:
    def test_task_starts_incomplete(self, sample_task: Task) -> None:
        """A newly created task should not be marked as completed."""
        assert sample_task.is_completed is False

    def test_complete_marks_task_done(self, sample_task: Task) -> None:
        """Calling complete() should set is_completed to True."""
        sample_task.complete()
        assert sample_task.is_completed is True

    def test_complete_is_idempotent(self, sample_task: Task) -> None:
        """Calling complete() twice should leave is_completed True."""
        sample_task.complete()
        sample_task.complete()
        assert sample_task.is_completed is True

    def test_to_dict_contains_all_fields(self, sample_task: Task) -> None:
        """to_dict() should include all five expected keys."""
        d = sample_task.to_dict()
        assert set(d.keys()) == {"name", "category", "duration_minutes", "priority", "is_completed"}

    def test_to_dict_reflects_current_state(self, sample_task: Task) -> None:
        """to_dict() values should match the task's current attributes."""
        sample_task.complete()
        d = sample_task.to_dict()
        assert d["name"] == "Morning walk"
        assert d["is_completed"] is True


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

class TestPet:
    def test_pet_starts_with_no_tasks(self, sample_pet: Pet) -> None:
        """A new pet should have an empty task list."""
        assert len(sample_pet.get_tasks()) == 0

    def test_add_task_increases_count(self, sample_pet: Pet, sample_task: Task) -> None:
        """Adding a task should increase the pet's task count by one."""
        sample_pet.add_task(sample_task)
        assert len(sample_pet.get_tasks()) == 1

    def test_add_multiple_tasks(self, sample_pet: Pet) -> None:
        """Adding three tasks should result in a task count of three."""
        for i in range(3):
            sample_pet.add_task(Task(name=f"Task {i}", category="walk", duration_minutes=10, priority=i + 1))
        assert len(sample_pet.get_tasks()) == 3

    def test_remove_task_decreases_count(self, sample_pet: Pet, sample_task: Task) -> None:
        """Removing an existing task should decrease the pet's task count."""
        sample_pet.add_task(sample_task)
        sample_pet.remove_task("Morning walk")
        assert len(sample_pet.get_tasks()) == 0

    def test_remove_nonexistent_task_is_safe(self, sample_pet: Pet) -> None:
        """Removing a task that doesn't exist should not raise an error."""
        sample_pet.remove_task("Ghost task")  # should not raise
        assert len(sample_pet.get_tasks()) == 0


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

class TestOwner:
    def test_add_pet_links_owner(self, owner_with_pet: Owner, sample_pet: Pet) -> None:
        """After add_pet(), the pet's owner attribute should point back to the owner."""
        assert sample_pet.owner is owner_with_pet

    def test_get_available_time_returns_budget(self) -> None:
        """get_available_time() should return the value set at construction."""
        owner = Owner(name="Alex", available_time_minutes=60)
        assert owner.get_available_time() == 60

    def test_get_all_tasks_flattens_across_pets(self) -> None:
        """get_all_tasks() should return tasks from all registered pets."""
        owner = Owner(name="Sam", available_time_minutes=120)
        dog = Pet(name="Rex", species="dog", age=2)
        cat = Pet(name="Mittens", species="cat", age=4)
        dog.add_task(Task(name="Walk", category="walk", duration_minutes=20, priority=1))
        cat.add_task(Task(name="Feed", category="feeding", duration_minutes=5, priority=2))
        owner.add_pet(dog)
        owner.add_pet(cat)
        assert len(owner.get_all_tasks()) == 2


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

class TestScheduler:
    def test_scheduler_uses_owner_budget_by_default(self, sample_pet: Pet) -> None:
        """Scheduler should inherit time budget from the pet's owner when not specified."""
        owner = Owner(name="Jordan", available_time_minutes=45)
        owner.add_pet(sample_pet)
        scheduler = Scheduler(sample_pet)
        assert scheduler.time_budget_minutes == 45

    def test_explicit_budget_overrides_owner(self, sample_pet: Pet) -> None:
        """An explicitly passed budget should take precedence over the owner's budget."""
        owner = Owner(name="Jordan", available_time_minutes=90)
        owner.add_pet(sample_pet)
        scheduler = Scheduler(sample_pet, time_budget_minutes=30)
        assert scheduler.time_budget_minutes == 30

    def test_all_tasks_fit_within_budget(self, sample_pet: Pet) -> None:
        """Tasks whose total time is within the budget should all be scheduled."""
        sample_pet.add_task(Task(name="Walk",  category="walk",    duration_minutes=20, priority=1))
        sample_pet.add_task(Task(name="Feed",  category="feeding", duration_minutes=10, priority=2))
        scheduler = Scheduler(sample_pet, time_budget_minutes=60)
        scheduled = scheduler.generate_schedule()
        assert len(scheduled) == 2
        assert len(scheduler.unscheduled_tasks) == 0

    def test_tasks_exceeding_budget_are_skipped(self, sample_pet: Pet) -> None:
        """Tasks that don't fit in the remaining budget should land in unscheduled_tasks."""
        sample_pet.add_task(Task(name="Walk",  category="walk",    duration_minutes=50, priority=1))
        sample_pet.add_task(Task(name="Bath",  category="grooming",duration_minutes=40, priority=2))
        scheduler = Scheduler(sample_pet, time_budget_minutes=60)
        scheduler.generate_schedule()
        assert len(scheduler.unscheduled_tasks) == 1
        assert scheduler.unscheduled_tasks[0].name == "Bath"

    def test_tasks_sorted_by_priority(self, sample_pet: Pet) -> None:
        """Scheduled tasks should appear in priority order (lowest number first)."""
        sample_pet.add_task(Task(name="Low",  category="walk",    duration_minutes=10, priority=3))
        sample_pet.add_task(Task(name="High", category="feeding", duration_minutes=10, priority=1))
        scheduler = Scheduler(sample_pet, time_budget_minutes=60)
        scheduled = scheduler.generate_schedule()
        assert scheduled[0].name == "High"
        assert scheduled[1].name == "Low"

    def test_explain_plan_mentions_budget(self, sample_pet: Pet) -> None:
        """explain_plan() output should reference the time budget."""
        sample_pet.add_task(Task(name="Walk", category="walk", duration_minutes=15, priority=1))
        scheduler = Scheduler(sample_pet, time_budget_minutes=60)
        scheduler.generate_schedule()
        explanation = scheduler.explain_plan()
        assert "60" in explanation

    def test_explain_plan_before_generate_warns(self, sample_pet: Pet) -> None:
        """explain_plan() called before generate_schedule() should return a warning string."""
        scheduler = Scheduler(sample_pet, time_budget_minutes=60)
        result = scheduler.explain_plan()
        assert "generate_schedule" in result
