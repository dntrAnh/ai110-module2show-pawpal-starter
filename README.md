# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Smarter Scheduling

The scheduler goes beyond a simple priority list with four added capabilities:

| Feature | How it works |
|---|---|
| **Sort by time** | `Scheduler.sort_by_time()` orders scheduled tasks chronologically using a lambda key on `"HH:MM"` strings; tasks without a start time appear last. |
| **Filter tasks** | `Scheduler.filter_tasks()` is a static method accepting keyword arguments (`completed`, `category`, `pet`) to return any subset of a task list without mutating the original. |
| **Recurring tasks** | `Task` has a `frequency` field (`"none"` / `"daily"` / `"weekly"`). Calling `complete()` sets `next_due` via `timedelta`; `spawn_next()` returns a fresh copy for the next occurrence. `generate_schedule()` automatically promotes these copies back onto the pet's task list. |
| **Conflict detection** | `Scheduler.detect_conflicts()` compares every pair of timed tasks. A conflict is raised whenever two windows overlap (start < other_end and other_start < end), returning a list of human-readable warning strings rather than raising an exception. |

---

## Testing PawPal+

### Run the test suite

```bash
python3 -m pytest
```

Or for verbose output showing each test name:

```bash
python3 -m pytest tests/ -v
```

### What the tests cover

The test suite (`tests/test_pawpal.py`) contains **39 tests** across 7 test classes:

| Class | # Tests | What it verifies |
|---|---|---|
| `TestTask` | 5 | Task creation, `complete()` idempotence, `to_dict()` correctness |
| `TestPet` | 5 | Task add/remove, task list isolation |
| `TestOwner` | 3 | Budget retrieval, pet back-linking, task flattening across pets |
| `TestScheduler` | 7 | Budget inheritance, priority ordering, greedy fit, `explain_plan()` output, edge cases (empty pet, zero budget) |
| `TestSorting` | 3 | `sort_by_time()` chronological order, unscheduled tasks last, empty-list safety |
| `TestRecurrence` | 6 | `complete()` sets `next_due` for daily/weekly tasks, `spawn_next()` produces a fresh copy, `generate_schedule()` auto-promotes recurring tasks |
| `TestConflictDetection` | 4 | No false positives for non-overlapping tasks, same start-time flagged, overlapping window flagged, tasks with no `start_time` ignored |
| `TestFilterTasks` | 4 | Filtering by `completed` status (True/False) and `category`, empty-list safety |

### Confidence level

★★★★☆ (4/5)

The critical paths (priority scheduling, recurring task spawning, overlap detection) are all covered by automated tests. The one remaining gap is end-to-end Streamlit UI testing — interactive widget behavior is not yet covered by the `pytest` suite.

