import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session-state bootstrap
# st.session_state persists data across reruns for the lifetime of the browser
# tab. We only create the Owner once; subsequent reruns reuse the same object.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None          # set after the owner form is submitted

# ---------------------------------------------------------------------------
# Section 1: Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner Setup")

with st.form("owner_form"):
    col_name, col_time = st.columns(2)
    with col_name:
        owner_name = st.text_input("Your name", value="Jordan")
    with col_time:
        available_minutes = st.number_input(
            "Daily time available (minutes)", min_value=10, max_value=480, value=90, step=5
        )
    submitted_owner = st.form_submit_button("Save owner")

if submitted_owner:
    # Replace the stored owner with the new values (preserves pets if name didn't change)
    existing: Owner | None = st.session_state.owner
    if existing is None or existing.name != owner_name:
        st.session_state.owner = Owner(name=owner_name, available_time_minutes=available_minutes)
    else:
        existing.available_time_minutes = available_minutes
    st.success(f"Owner **{owner_name}** saved with {available_minutes} min/day.")

owner: Owner | None = st.session_state.owner
if owner is None:
    st.info("Fill in your details above and click **Save owner** to get started.")
    st.stop()

st.caption(f"Active owner: **{owner.name}** · {owner.get_available_time()} min/day · {len(owner.pets)} pet(s)")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add a pet
# ---------------------------------------------------------------------------
st.header("2. Add a Pet")

with st.form("pet_form"):
    col_pname, col_species, col_age = st.columns(3)
    with col_pname:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col_species:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col_age:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    submitted_pet = st.form_submit_button("Add pet")

if submitted_pet:
    # Avoid duplicate pet names for this owner
    existing_names = [p.name for p in owner.pets]
    if pet_name in existing_names:
        st.warning(f"**{pet_name}** is already in your pet list.")
    else:
        new_pet = Pet(name=pet_name, species=species, age=age)
        owner.add_pet(new_pet)          # sets new_pet.owner = owner automatically
        st.success(f"Added **{pet_name}** the {species}!")

if owner.pets:
    st.write("Your pets:")
    st.table([{"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.get_tasks())} for p in owner.pets])

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Add tasks to a pet
# ---------------------------------------------------------------------------
st.header("3. Add Tasks")

if not owner.pets:
    st.info("Add at least one pet above before adding tasks.")
else:
    with st.form("task_form"):
        selected_pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
        col_t, col_cat = st.columns(2)
        col_dur, col_pri = st.columns(2)
        col_freq, col_time_input = st.columns(2)
        with col_t:
            task_name = st.text_input("Task name", value="Morning walk")
        with col_cat:
            category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment", "other"])
        with col_dur:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col_pri:
            priority = st.number_input("Priority (1 = highest)", min_value=1, max_value=10, value=2)
        with col_freq:
            frequency = st.selectbox("Recurrence", ["none", "daily", "weekly"])
        with col_time_input:
            start_time = st.text_input("Start time (HH:MM, optional)", value="", placeholder="e.g. 07:30")
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        # Validate HH:MM format if provided
        st_clean = start_time.strip()
        valid_time = True
        if st_clean:
            parts = st_clean.split(":")
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                st.error("Start time must be in HH:MM format (e.g. 07:30).")
                valid_time = False
            else:
                h, m = int(parts[0]), int(parts[1])
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    st.error("Start time hour must be 0–23 and minutes 0–59.")
                    valid_time = False
        if valid_time:
            target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
            target_pet.add_task(
                Task(
                    name=task_name,
                    category=category,
                    duration_minutes=int(duration),
                    priority=int(priority),
                    frequency=frequency,
                    start_time=st_clean,
                )
            )
            st.success(
                f"Added **{task_name}** to {selected_pet_name}"
                + (f" · repeats {frequency}" if frequency != "none" else "")
                + (f" · starts {st_clean}" if st_clean else "")
                + "."
            )

    # Show all tasks across all pets
    all_rows = []
    for p in owner.pets:
        for t in p.get_tasks():
            all_rows.append({
                "Pet": p.name,
                "Task": t.name,
                "Category": t.category,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Start time": t.start_time or "—",
                "Recurrence": t.frequency,
                "Done": "✓" if t.is_completed else "",
            })
    if all_rows:
        st.write("All tasks:")
        st.table(all_rows)
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Generate schedule
# ---------------------------------------------------------------------------
st.header("4. Generate Today's Schedule")

if not owner.pets or not owner.get_all_tasks():
    st.info("Add at least one pet and one task before generating a schedule.")
else:
    # Optional filter controls (shown outside the form so they persist across reruns)
    with st.expander("⚙️ Filter & view options", expanded=False):
        filter_category = st.selectbox(
            "Show only category", ["(all)", "walk", "feeding", "medication", "grooming", "enrichment", "other"]
        )
        sort_by_time_toggle = st.checkbox("Sort results by start time (chronological)", value=True)

    if st.button("Generate schedule", type="primary"):
        for pet in owner.pets:
            if not pet.get_tasks():
                continue
            scheduler = Scheduler(pet)       # inherits owner's time budget automatically
            scheduler.generate_schedule()

            st.subheader(f"📅 {pet.name} ({pet.species})")

            # ---- Conflict detection ----
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                for warning in conflicts:
                    st.warning(warning)
            else:
                st.success("✅ No scheduling conflicts detected.")

            # ---- Build display rows ----
            tasks_to_show = list(scheduler.scheduled_tasks)

            # Apply category filter
            if filter_category != "(all)":
                tasks_to_show = Scheduler.filter_tasks(tasks_to_show, category=filter_category)

            # Apply time sort
            if sort_by_time_toggle:
                tasks_to_show = scheduler.sort_by_time(tasks_to_show)

            if tasks_to_show:
                scheduled_rows = []
                for t in tasks_to_show:
                    scheduled_rows.append({
                        "Task": t.name,
                        "Category": t.category,
                        "Start time": t.start_time or "—",
                        "Duration (min)": t.duration_minutes,
                        "Priority": t.priority,
                        "Recurrence": t.frequency,
                        "Done": "✓" if t.is_completed else "",
                    })
                st.table(scheduled_rows)
            else:
                if filter_category != "(all)":
                    st.info(f"No scheduled tasks in category **{filter_category}** for {pet.name}.")
                else:
                    st.info(f"No tasks could be scheduled for {pet.name} within the time budget.")

            # ---- Unscheduled tasks ----
            if scheduler.unscheduled_tasks:
                with st.expander(f"⏭️ {len(scheduler.unscheduled_tasks)} task(s) skipped (over budget)"):
                    skipped_rows = [
                        {
                            "Task": t.name,
                            "Category": t.category,
                            "Duration (min)": t.duration_minutes,
                            "Priority": t.priority,
                        }
                        for t in scheduler.unscheduled_tasks
                    ]
                    st.table(skipped_rows)

            # ---- Plain-English explanation ----
            with st.expander("🗒️ Scheduling explanation"):
                st.code(scheduler.explain_plan(), language=None)

        # ---- Cross-pet budget summary ----
        total_time = sum(t.duration_minutes for t in owner.get_all_tasks())
        budget = owner.get_available_time()
        st.divider()
        if total_time > budget:
            st.warning(
                f"⚠️ Total task time across all pets ({total_time} min) exceeds your daily budget "
                f"({budget} min). Lower-priority tasks will be skipped."
            )
        else:
            st.success(
                f"✅ All tasks fit within your {budget}-minute daily budget "
                f"(total: {total_time} min)."
            )

st.divider()

# ---------------------------------------------------------------------------
# Section 5: Find next available slot
# ---------------------------------------------------------------------------
st.header("5. Find Next Available Slot")
st.caption(
    "Given a task duration and a search window, the scheduler scans existing "
    "timed tasks and returns the first free time slot that fits—no overlap guaranteed."
)

if not owner.pets or not owner.get_all_tasks():
    st.info("Generate a schedule above before using the slot finder.")
else:
    with st.form("slot_finder_form"):
        col_pet_slot, col_dur_slot = st.columns(2)
        col_from, col_to = st.columns(2)
        with col_pet_slot:
            slot_pet_name = st.selectbox("Pet to check", [p.name for p in owner.pets], key="slot_pet")
        with col_dur_slot:
            slot_duration = st.number_input("Task duration (min)", min_value=1, max_value=240, value=30, key="slot_dur")
        with col_from:
            slot_search_from = st.text_input("Search from (HH:MM)", value="07:00", key="slot_from")
        with col_to:
            slot_end_by = st.text_input("End by (HH:MM)", value="22:00", key="slot_to")
        find_slot_btn = st.form_submit_button("🔍 Find next available slot")

    if find_slot_btn:
        target_pet = next(p for p in owner.pets if p.name == slot_pet_name)
        slot_scheduler = Scheduler(target_pet)
        slot_scheduler.generate_schedule()
        try:
            slot = slot_scheduler.find_next_slot(
                duration_minutes=int(slot_duration),
                search_from=slot_search_from.strip(),
                end_by=slot_end_by.strip(),
            )
            if slot:
                slot_end_mins = int(slot.split(":")[0]) * 60 + int(slot.split(":")[1]) + int(slot_duration)
                slot_end_str = f"{slot_end_mins // 60:02d}:{slot_end_mins % 60:02d}"
                st.success(
                    f"✅ Next free slot for **{slot_pet_name}**: "
                    f"**{slot} – {slot_end_str}** ({int(slot_duration)} min)"
                )
            else:
                st.warning(
                    f"No free {int(slot_duration)}-minute slot found for **{slot_pet_name}** "
                    f"between {slot_search_from} and {slot_end_by}. "
                    "Try extending the search window or shortening the duration."
                )
        except ValueError as exc:
            st.error(f"Invalid input: {exc}")

