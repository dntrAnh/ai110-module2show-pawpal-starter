"""
main.py — PawPal+ demo script
Demonstrates: scheduling, sort_by_time, filter_tasks, recurring tasks, conflict detection.
Run:  python3 main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler

DIVIDER = "─" * 55

# ── Owner & Pets ───────────────────────────────────────────────────────────
jordan = Owner(name="Jordan", available_time_minutes=120)

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

jordan.add_pet(mochi)
jordan.add_pet(luna)

# ── Tasks for Mochi (intentionally out of chronological order) ─────────────
mochi.add_task(Task(name="Evening walk",   category="walk",       duration_minutes=25, priority=2, start_time="18:00"))
mochi.add_task(Task(name="Breakfast",      category="feeding",    duration_minutes=10, priority=2, start_time="07:30", frequency="daily"))
mochi.add_task(Task(name="Heartworm pill", category="medication", duration_minutes=5,  priority=1, start_time="07:35"))
mochi.add_task(Task(name="Morning walk",   category="walk",       duration_minutes=30, priority=1, start_time="07:00"))
# Conflict: Training overlaps Evening walk (18:00–18:25)
mochi.add_task(Task(name="Training",       category="enrichment", duration_minutes=20, priority=3, start_time="18:10"))

# ── Tasks for Luna ─────────────────────────────────────────────────────────
luna.add_task(Task(name="Breakfast",        category="feeding",   duration_minutes=5,  priority=2, start_time="08:00", frequency="daily"))
luna.add_task(Task(name="Litter box clean", category="grooming",  duration_minutes=10, priority=2, start_time="09:00", frequency="weekly"))
luna.add_task(Task(name="Flea treatment",   category="medication",duration_minutes=5,  priority=1, start_time="08:05"))

# ── 1. Generate schedule (priority-based fit within time budget) ───────────
print("\n" + DIVIDER)
print("1. PRIORITY-BASED SCHEDULE")
print(DIVIDER)
for pet in jordan.pets:
    scheduler = Scheduler(pet)
    scheduler.generate_schedule()
    print(f"\n📅  {pet.name} ({pet.species})")
    print(scheduler.explain_plan())

# ── 2. Sort by start_time ──────────────────────────────────────────────────
print("\n" + DIVIDER)
print("2. MOCHI'S SCHEDULE SORTED BY START TIME")
print(DIVIDER)
mochi_scheduler = Scheduler(mochi)
mochi_scheduler.generate_schedule()
sorted_tasks = mochi_scheduler.sort_by_time()
for t in sorted_tasks:
    time_label = t.start_time if t.start_time else "(no time)"
    print(f"  {time_label}  [{t.priority}] {t.name} — {t.duration_minutes} min")

# ── 3. Filter tasks ────────────────────────────────────────────────────────
print("\n" + DIVIDER)
print("3. FILTERING")
print(DIVIDER)

all_tasks = jordan.get_all_tasks()

pending = Scheduler.filter_tasks(all_tasks, completed=False)
print(f"  Pending tasks across all pets : {len(pending)}")

walks = Scheduler.filter_tasks(all_tasks, category="walk")
print(f"  Walk tasks                    : {[t.name for t in walks]}")

mochi_tasks = Scheduler.filter_tasks(all_tasks, pet=mochi)
print(f"  Mochi's tasks                 : {[t.name for t in mochi_tasks]}")

# ── 4. Recurring tasks ─────────────────────────────────────────────────────
print("\n" + DIVIDER)
print("4. RECURRING TASKS — complete Mochi's Breakfast, spawn tomorrow's copy")
print(DIVIDER)
breakfast = next(t for t in mochi.get_tasks() if t.name == "Breakfast")
print(f"  Before: is_completed={breakfast.is_completed}, next_due={breakfast.next_due}")
breakfast.complete()
print(f"  After : is_completed={breakfast.is_completed}, next_due={breakfast.next_due}")
next_copy = breakfast.spawn_next()
if next_copy:
    print(f"  Spawned new task: '{next_copy.name}' due {next_copy.next_due} (frequency={next_copy.frequency})")

# ── 5. Conflict detection ──────────────────────────────────────────────────
print("\n" + DIVIDER)
print("5. CONFLICT DETECTION (Mochi)")
print(DIVIDER)
# Re-run schedule to pick up the conflicting tasks
conflict_scheduler = Scheduler(mochi)
conflict_scheduler.generate_schedule()
conflicts = conflict_scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")

print("\n" + DIVIDER + "\n")
