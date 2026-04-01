"""
main.py — PawPal+ demo script
Run:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler

# ── Owner ──────────────────────────────────────────────────────────────────
jordan = Owner(name="Jordan", available_time_minutes=90)

# ── Pets ───────────────────────────────────────────────────────────────────
mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

jordan.add_pet(mochi)
jordan.add_pet(luna)

# ── Tasks for Mochi ────────────────────────────────────────────────────────
mochi.add_task(Task(name="Morning walk",    category="walk",      duration_minutes=30, priority=1))
mochi.add_task(Task(name="Breakfast",       category="feeding",   duration_minutes=10, priority=2))
mochi.add_task(Task(name="Heartworm pill",  category="medication",duration_minutes=5,  priority=1))
mochi.add_task(Task(name="Enrichment play", category="enrichment",duration_minutes=20, priority=3))

# ── Tasks for Luna ─────────────────────────────────────────────────────────
luna.add_task(Task(name="Breakfast",        category="feeding",   duration_minutes=5,  priority=2))
luna.add_task(Task(name="Litter box clean", category="grooming",  duration_minutes=10, priority=2))
luna.add_task(Task(name="Flea treatment",   category="medication",duration_minutes=5,  priority=1))

# ── Schedule each pet ──────────────────────────────────────────────────────
DIVIDER = "─" * 50

for pet in jordan.pets:
    scheduler = Scheduler(pet)          # time budget comes from jordan automatically
    scheduler.generate_schedule()

    print(DIVIDER)
    print(f"📅  Today's Schedule for {pet.name} ({pet.species})")
    print(DIVIDER)
    print(scheduler.explain_plan())
    print()

# ── Summary across all pets ────────────────────────────────────────────────
all_tasks = jordan.get_all_tasks()
total_time = sum(t.duration_minutes for t in all_tasks)
print(DIVIDER)
print(f"🐾  {jordan.name}'s total care time across all pets: {total_time} min")
print(f"    Daily budget: {jordan.get_available_time()} min")
if total_time > jordan.get_available_time():
    print("    ⚠️  Total task time exceeds daily budget — some tasks will be skipped.")
else:
    print("    ✅  All tasks fit within the daily budget.")
print(DIVIDER)
