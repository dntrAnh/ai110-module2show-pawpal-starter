# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Features

| Feature | Description |
|---|---|
| **Owner & pet setup** | Register an owner with a daily time budget and add any number of pets (dog, cat, other). |
| **Task management** | Add care tasks with name, category, duration, priority, optional start time, and recurrence (none / daily / weekly). Tasks are displayed in a live table. |
| **Priority scheduling** | Tasks are ranked by priority (1 = highest) and greedily packed into the owner's time budget. Low-priority tasks that don't fit are collected in a "skipped" list. |
| **Sort by time** | Scheduled tasks can be displayed in chronological order using `Scheduler.sort_by_time()`, with unscheduled tasks always appearing last. |
| **Category filter** | A dropdown filter lets you view only tasks of a specific type (walk, feeding, medication, etc.) using `Scheduler.filter_tasks()`. |
| **Recurring tasks** | Daily and weekly tasks auto-schedule their next occurrence. Completing a task sets `next_due` via `timedelta`; `generate_schedule()` promotes the spawned copy automatically. |
| **Conflict warnings** | `Scheduler.detect_conflicts()` scans timed tasks for overlapping windows and surfaces each conflict as a `st.warning` banner in the UI. |
| **Plain-English explanation** | `explain_plan()` produces a human-readable summary of what was scheduled, what was skipped, and why. |
| **Next available slot** | `Scheduler.find_next_slot(duration, search_from, end_by)` scans existing timed tasks and returns the earliest free `"HH:MM"` window that fits the requested duration without conflicting with any occupied interval. Surfaced in the UI as a dedicated "Find Next Available Slot" tool. |
| **Data persistence** | `Owner.save_to_json(filepath)` serialises the full owner → pets → tasks graph to a JSON file using an atomic write (`tmp` → `os.replace()`). `Owner.load_from_json(filepath)` deserialises it back, restoring every `next_due` date and the `pet.owner` back-link. The Streamlit app auto-loads `data.json` on startup and auto-saves after every mutation. |

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

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
| **JSON persistence** | `Owner.to_dict()` / `Owner.from_dict()` / `Pet.to_dict()` / `Pet.from_dict()` / `Task.from_dict()` implement a full serialisation round-trip. `save_to_json()` writes atomically via a `.tmp` file and `os.replace()` to prevent partial writes on crash. `load_from_json()` returns `None` for a missing file and raises `ValueError` for corrupt JSON. |

---

## Agent Mode: How `find_next_slot` Was Built

The **Next Available Slot** algorithm was developed using GitHub Copilot in **Agent Mode**, which allowed the AI to autonomously plan, implement, test, and document the feature across multiple files in a single session without manual hand-off between steps.

### What Agent Mode did

| Step | Action taken by Agent Mode |
|---|---|
| **Explored context** | Read `pawpal_system.py`, `app.py`, `tests/test_pawpal.py`, and `main.py` in parallel to understand existing patterns before writing a single line. |
| **Designed the algorithm** | Proposed an interval-scanning approach: build a sorted list of `(start, end)` occupied tuples from timed tasks, then walk candidate start times in 1-minute steps, jumping to the end of each blocking interval rather than incrementing one minute at a time (O(tasks) instead of O(minutes × tasks)). |
| **Implemented across files** | Added `find_next_slot()` to `Scheduler` in `pawpal_system.py`; added Section 5 to `app.py`; added a demo block to `main.py`; added `TestFindNextSlot` (6 tests) to `test_pawpal.py`; updated `README.md` — all as coordinated edits in one turn. |
| **Validated immediately** | Ran `python3 -m pytest tests/ -v` after each file change. All 45 tests passed on the first run with no post-hoc fixes. |
| **Documented tradeoffs** | Noted that tasks without a `start_time` are invisble to the slot scanner (by design), and explained this tradeoff in reflection.md. |

### Why Agent Mode was the right tool here

This feature required **cross-file coherence** — the algorithm itself, its test cases, its UI wiring, and its demo all had to agree on the same API signature (`duration_minutes, search_from, end_by`). In standard Chat mode that coordination is manual; you paste each file in turn and stitch the outputs yourself. Agent Mode maintained a consistent mental model of all four files simultaneously, which meant the function signature was never mismatched between the implementation and the tests.

The key human judgment call was the **jump-to-end-of-block optimization**: Copilot's first draft incremented `candidate` by 1 minute per iteration, which would have been correct but slow for large schedules. The architect (human) directed Agent Mode to instead jump `candidate` forward to `occ_end` whenever a blocking interval was found, reducing inner-loop iterations from O(minutes) to O(tasks).

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

The test suite (`tests/test_pawpal.py`) contains **53 tests** across 9 test classes:

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
| `TestFindNextSlot` | 6 | Earliest free slot scanning, gap detection, `end_by` boundary enforcement, `ValueError` on invalid duration |
| `TestPersistence` | 8 | Full owner/pet/task round-trip, `next_due` date serialisation, `owner` back-link restoration, missing-file returns `None`, corrupt JSON raises `ValueError`, raw JSON structure |

### Confidence level

★★★★☆ (4/5)

The critical paths (priority scheduling, recurring task spawning, overlap detection) are all covered by automated tests. The one remaining gap is end-to-end Streamlit UI testing — interactive widget behavior is not yet covered by the `pytest` suite.

