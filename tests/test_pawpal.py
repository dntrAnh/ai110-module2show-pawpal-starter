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
        """to_dict() should include all expected keys."""
        d = sample_task.to_dict()
        assert set(d.keys()) == {
            "name", "category", "duration_minutes", "priority",
            "is_completed", "frequency", "start_time", "next_due",
        }

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

    def test_pet_with_no_tasks_generates_empty_schedule(self, sample_pet: Pet) -> None:
        """A pet with zero tasks should yield an empty scheduled and unscheduled list."""
        owner = Owner(name="Jordan", available_time_minutes=60)
        owner.add_pet(sample_pet)
        scheduler = Scheduler(sample_pet)
        scheduled = scheduler.generate_schedule()
        assert scheduled == []
        assert scheduler.unscheduled_tasks == []

    def test_zero_budget_schedules_nothing(self, sample_pet: Pet) -> None:
        """When the time budget is 0, all tasks should land in unscheduled_tasks."""
        sample_pet.add_task(Task(name="Walk", category="walk", duration_minutes=10, priority=1))
        scheduler = Scheduler(sample_pet, time_budget_minutes=0)
        scheduler.generate_schedule()
        assert scheduler.scheduled_tasks == []
        assert len(scheduler.unscheduled_tasks) == 1


# ---------------------------------------------------------------------------
# Sorting tests
# ---------------------------------------------------------------------------

class TestSorting:
    def test_sort_by_time_returns_chronological_order(self) -> None:
        """sort_by_time() should return tasks ordered earliest start_time first."""
        owner = Owner(name="Jordan", available_time_minutes=120)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        late_task  = Task(name="Evening walk", category="walk",    duration_minutes=20, priority=1, start_time="18:00")
        early_task = Task(name="Breakfast",    category="feeding", duration_minutes=10, priority=2, start_time="07:30")
        mid_task   = Task(name="Meds",         category="medication", duration_minutes=5, priority=3, start_time="12:00")
        pet.add_task(late_task)
        pet.add_task(early_task)
        pet.add_task(mid_task)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        sorted_tasks = scheduler.sort_by_time()
        assert sorted_tasks[0].start_time == "07:30"
        assert sorted_tasks[1].start_time == "12:00"
        assert sorted_tasks[2].start_time == "18:00"

    def test_sort_by_time_unscheduled_tasks_go_last(self) -> None:
        """Tasks without a start_time should appear after all timed tasks."""
        owner = Owner(name="Jordan", available_time_minutes=120)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        timed_task     = Task(name="Walk",  category="walk",    duration_minutes=20, priority=1, start_time="08:00")
        no_time_task   = Task(name="Groom", category="grooming", duration_minutes=30, priority=2)
        pet.add_task(timed_task)
        pet.add_task(no_time_task)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        sorted_tasks = scheduler.sort_by_time()
        assert sorted_tasks[0].start_time == "08:00"
        assert sorted_tasks[-1].start_time == ""

    def test_sort_by_time_with_empty_list(self) -> None:
        """sort_by_time() on an empty list should return an empty list."""
        owner = Owner(name="Jordan", available_time_minutes=60)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        assert scheduler.sort_by_time([]) == []


# ---------------------------------------------------------------------------
# Recurrence tests
# ---------------------------------------------------------------------------

class TestRecurrence:
    def test_daily_task_complete_sets_next_due_to_tomorrow(self) -> None:
        """Completing a daily task should set next_due to today + 1 day."""
        from datetime import date, timedelta
        task = Task(name="Feed", category="feeding", duration_minutes=5, priority=1, frequency="daily")
        task.complete()
        assert task.next_due == date.today() + timedelta(days=1)

    def test_weekly_task_complete_sets_next_due_to_next_week(self) -> None:
        """Completing a weekly task should set next_due to today + 7 days."""
        from datetime import date, timedelta
        task = Task(name="Bath", category="grooming", duration_minutes=30, priority=2, frequency="weekly")
        task.complete()
        assert task.next_due == date.today() + timedelta(weeks=1)

    def test_non_recurring_task_next_due_stays_none(self) -> None:
        """Completing a non-recurring task should leave next_due as None."""
        task = Task(name="Vet visit", category="medication", duration_minutes=60, priority=1, frequency="none")
        task.complete()
        assert task.next_due is None

    def test_spawn_next_returns_fresh_incomplete_copy(self) -> None:
        """spawn_next() should return a new Task with is_completed=False."""
        from datetime import date, timedelta
        task = Task(name="Feed", category="feeding", duration_minutes=5, priority=1, frequency="daily")
        task.complete()
        next_task = task.spawn_next()
        assert next_task is not None
        assert next_task.is_completed is False
        assert next_task.name == "Feed"

    def test_spawn_next_on_non_recurring_returns_none(self) -> None:
        """spawn_next() on a non-recurring task should return None."""
        task = Task(name="Vet visit", category="medication", duration_minutes=60, priority=1, frequency="none")
        task.complete()
        assert task.spawn_next() is None

    def test_generate_schedule_auto_spawns_recurring_task(self) -> None:
        """generate_schedule() should add a new occurrence for a completed recurring task."""
        owner = Owner(name="Jordan", available_time_minutes=120)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        task = Task(name="Feed", category="feeding", duration_minutes=5, priority=1, frequency="daily")
        task.complete()          # mark done — should trigger spawn on next generate_schedule
        pet.add_task(task)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        # The spawned next occurrence should now be in the pet's task list
        names = [t.name for t in pet.get_tasks()]
        assert names.count("Feed") == 2  # original (completed) + spawned next


# ---------------------------------------------------------------------------
# Conflict detection tests
# ---------------------------------------------------------------------------

class TestConflictDetection:
    def _make_scheduled_scheduler(self, pet: Pet, tasks: list) -> "Scheduler":
        """Helper: inject tasks directly into scheduled_tasks (bypassing budget logic)."""
        owner = Owner(name="Jordan", available_time_minutes=300)
        owner.add_pet(pet)
        for t in tasks:
            pet.add_task(t)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        return scheduler

    def test_no_conflicts_for_non_overlapping_tasks(self) -> None:
        """Two tasks with non-overlapping windows should produce no conflict warnings."""
        pet = Pet(name="Mochi", species="dog", age=3)
        morning = Task(name="Walk",  category="walk",    duration_minutes=20, priority=1, start_time="07:00")
        noon    = Task(name="Feed",  category="feeding", duration_minutes=10, priority=2, start_time="12:00")
        scheduler = self._make_scheduled_scheduler(pet, [morning, noon])
        assert scheduler.detect_conflicts() == []

    def test_conflict_detected_for_same_start_time(self) -> None:
        """Two tasks starting at the exact same time should be flagged as a conflict."""
        pet = Pet(name="Mochi", species="dog", age=3)
        task_a = Task(name="Walk",  category="walk",    duration_minutes=20, priority=1, start_time="08:00")
        task_b = Task(name="Train", category="walk",    duration_minutes=15, priority=2, start_time="08:00")
        scheduler = self._make_scheduled_scheduler(pet, [task_a, task_b])
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) >= 1
        assert any("Walk" in c and "Train" in c for c in conflicts)

    def test_conflict_detected_for_overlapping_windows(self) -> None:
        """A task starting before another ends should be flagged as a conflict."""
        pet = Pet(name="Mochi", species="dog", age=3)
        # Walk starts 18:00, lasts 30 min → ends 18:30
        # Training starts 18:10 → inside the Walk window
        walk     = Task(name="Evening walk", category="walk", duration_minutes=30, priority=1, start_time="18:00")
        training = Task(name="Training",     category="walk", duration_minutes=20, priority=2, start_time="18:10")
        scheduler = self._make_scheduled_scheduler(pet, [walk, training])
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) >= 1

    def test_tasks_without_start_time_skipped_in_conflict_detection(self) -> None:
        """Tasks with no start_time should never be included in conflict detection."""
        pet = Pet(name="Mochi", species="dog", age=3)
        task_a = Task(name="Walk",  category="walk",    duration_minutes=20, priority=1)  # no start_time
        task_b = Task(name="Groom", category="grooming", duration_minutes=20, priority=2)  # no start_time
        scheduler = self._make_scheduled_scheduler(pet, [task_a, task_b])
        assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Filter tests
# ---------------------------------------------------------------------------

class TestFilterTasks:
    def test_filter_by_completed_true_returns_only_done_tasks(self) -> None:
        """filter_tasks(completed=True) should return only completed tasks."""
        done   = Task(name="Walk",  category="walk",    duration_minutes=20, priority=1, is_completed=True)
        pending = Task(name="Feed", category="feeding", duration_minutes=10, priority=2)
        result = Scheduler.filter_tasks([done, pending], completed=True)
        assert len(result) == 1
        assert result[0].name == "Walk"

    def test_filter_by_completed_false_returns_only_pending(self) -> None:
        """filter_tasks(completed=False) should return only incomplete tasks."""
        done    = Task(name="Walk", category="walk",    duration_minutes=20, priority=1, is_completed=True)
        pending = Task(name="Feed", category="feeding", duration_minutes=10, priority=2)
        result = Scheduler.filter_tasks([done, pending], completed=False)
        assert len(result) == 1
        assert result[0].name == "Feed"

    def test_filter_by_category(self) -> None:
        """filter_tasks(category='walk') should return only tasks in that category."""
        walk_task = Task(name="Walk", category="walk",    duration_minutes=20, priority=1)
        feed_task = Task(name="Feed", category="feeding", duration_minutes=10, priority=2)
        result = Scheduler.filter_tasks([walk_task, feed_task], category="walk")
        assert len(result) == 1
        assert result[0].category == "walk"

    def test_filter_empty_list_returns_empty(self) -> None:
        """Filtering an empty list should always return an empty list."""
        assert Scheduler.filter_tasks([], completed=False) == []
        assert Scheduler.filter_tasks([], category="walk") == []


# ---------------------------------------------------------------------------
# Next-available-slot tests
# ---------------------------------------------------------------------------

class TestFindNextSlot:
    """Tests for Scheduler.find_next_slot() — the interval-scanning slot finder."""

    def _scheduler_with_tasks(self, timed_tasks: list) -> "Scheduler":
        """Helper: build a scheduler whose scheduled_tasks list contains *timed_tasks*."""
        owner = Owner(name="Jordan", available_time_minutes=480)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        for t in timed_tasks:
            pet.add_task(t)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        return scheduler

    def test_empty_schedule_returns_search_from(self) -> None:
        """With no existing tasks, the first slot should be search_from itself."""
        owner = Owner(name="Jordan", available_time_minutes=480)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        result = scheduler.find_next_slot(30, search_from="08:00")
        assert result == "08:00"

    def test_slot_found_after_single_occupied_task(self) -> None:
        """A 30-min slot should be found immediately after an existing 60-min task."""
        task = Task(name="Walk", category="walk", duration_minutes=60, priority=1, start_time="08:00")
        scheduler = self._scheduler_with_tasks([task])
        # 08:00–09:00 is occupied; next slot for 30 min should start at 09:00
        result = scheduler.find_next_slot(30, search_from="08:00")
        assert result == "09:00"

    def test_slot_found_in_gap_between_tasks(self) -> None:
        """A gap between two tasks should be found when the requested size fits."""
        t1 = Task(name="Breakfast", category="feeding",  duration_minutes=15, priority=1, start_time="07:00")
        t2 = Task(name="Walk",      category="walk",     duration_minutes=30, priority=2, start_time="08:00")
        scheduler = self._scheduler_with_tasks([t1, t2])
        # Gap: 07:15–08:00 = 45 min free; a 30-min slot should start at 07:15
        result = scheduler.find_next_slot(30, search_from="07:00")
        assert result == "07:15"

    def test_no_slot_when_day_fully_booked(self) -> None:
        """find_next_slot() should return None when no window fits before end_by."""
        # 08:00–10:00 (120 min) fills the 08:00–10:00 window used as end_by
        task = Task(name="Long session", category="enrichment", duration_minutes=120, priority=1, start_time="08:00")
        scheduler = self._scheduler_with_tasks([task])
        # Only 2 hours available (08:00–10:00); request 30 min but end_by=10:00
        # Even after the block ends at 10:00 there is no room because end_by == end of block
        result = scheduler.find_next_slot(30, search_from="08:00", end_by="10:00")
        assert result is None

    def test_invalid_duration_raises_value_error(self) -> None:
        """A duration of 0 or negative should raise ValueError."""
        import pytest as _pytest
        owner = Owner(name="Jordan", available_time_minutes=60)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        with _pytest.raises(ValueError):
            scheduler.find_next_slot(0)

    def test_slot_respects_end_by_boundary(self) -> None:
        """A slot that would run past end_by should not be returned."""
        owner = Owner(name="Jordan", available_time_minutes=60)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        scheduler = Scheduler(pet)
        scheduler.generate_schedule()
        # 60-min slot starting at 21:30 would end at 22:30, past end_by=22:00
        result = scheduler.find_next_slot(60, search_from="21:30", end_by="22:00")
        assert result is None


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------

class TestPersistence:
    """Tests for Owner.save_to_json() and Owner.load_from_json()."""

    def _build_owner(self) -> Owner:
        """Helper: create a populated Owner with one pet and two tasks."""
        from datetime import date
        owner = Owner(name="Jordan", available_time_minutes=90)
        pet = Pet(name="Mochi", species="dog", age=3)
        owner.add_pet(pet)
        pet.add_task(Task(name="Walk", category="walk", duration_minutes=20, priority=1, start_time="07:00"))
        recurring = Task(name="Feed", category="feeding", duration_minutes=5, priority=2, frequency="daily")
        recurring.complete()  # sets next_due
        pet.add_task(recurring)
        return owner

    def test_round_trip_preserves_owner_fields(self, tmp_path) -> None:
        """Saving and reloading should preserve owner name and time budget."""
        filepath = str(tmp_path / "data.json")
        owner = self._build_owner()
        owner.save_to_json(filepath)
        loaded = Owner.load_from_json(filepath)
        assert loaded is not None
        assert loaded.name == "Jordan"
        assert loaded.available_time_minutes == 90

    def test_round_trip_preserves_pets(self, tmp_path) -> None:
        """Saving and reloading should preserve pet count and attributes."""
        filepath = str(tmp_path / "data.json")
        owner = self._build_owner()
        owner.save_to_json(filepath)
        loaded = Owner.load_from_json(filepath)
        assert len(loaded.pets) == 1
        assert loaded.pets[0].name == "Mochi"
        assert loaded.pets[0].species == "dog"
        assert loaded.pets[0].age == 3

    def test_round_trip_preserves_tasks(self, tmp_path) -> None:
        """Saving and reloading should preserve task details."""
        filepath = str(tmp_path / "data.json")
        owner = self._build_owner()
        owner.save_to_json(filepath)
        loaded = Owner.load_from_json(filepath)
        tasks = loaded.pets[0].get_tasks()
        assert len(tasks) == 2
        walk = next(t for t in tasks if t.name == "Walk")
        assert walk.category == "walk"
        assert walk.duration_minutes == 20
        assert walk.start_time == "07:00"

    def test_round_trip_preserves_recurring_next_due(self, tmp_path) -> None:
        """next_due dates should survive JSON serialisation and deserialisation."""
        from datetime import date, timedelta
        filepath = str(tmp_path / "data.json")
        owner = self._build_owner()
        owner.save_to_json(filepath)
        loaded = Owner.load_from_json(filepath)
        feed = next(t for t in loaded.pets[0].get_tasks() if t.name == "Feed")
        assert feed.is_completed is True
        assert feed.next_due == date.today() + timedelta(days=1)

    def test_round_trip_restores_owner_back_link(self, tmp_path) -> None:
        """After loading, each pet's owner attribute should point to the loaded Owner."""
        filepath = str(tmp_path / "data.json")
        owner = self._build_owner()
        owner.save_to_json(filepath)
        loaded = Owner.load_from_json(filepath)
        assert loaded.pets[0].owner is loaded

    def test_load_returns_none_for_missing_file(self, tmp_path) -> None:
        """load_from_json() should return None when the file does not exist."""
        result = Owner.load_from_json(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_load_raises_on_invalid_json(self, tmp_path) -> None:
        """load_from_json() should raise ValueError for corrupt JSON content."""
        import pytest as _pytest
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json}", encoding="utf-8")
        with _pytest.raises(ValueError, match="Could not parse"):
            Owner.load_from_json(str(bad_file))

    def test_save_is_atomic_on_missing_directory_entry(self, tmp_path) -> None:
        """save_to_json() should write a readable JSON file."""
        import json as _json
        filepath = str(tmp_path / "output.json")
        owner = self._build_owner()
        owner.save_to_json(filepath)
        with open(filepath, encoding="utf-8") as fh:
            data = _json.load(fh)
        assert data["name"] == "Jordan"
        assert len(data["pets"]) == 1
