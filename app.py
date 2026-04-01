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
        col_t, col_cat, col_dur, col_pri = st.columns(4)
        with col_t:
            task_name = st.text_input("Task name", value="Morning walk")
        with col_cat:
            category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment", "other"])
        with col_dur:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col_pri:
            priority = st.number_input("Priority (1 = highest)", min_value=1, max_value=10, value=2)
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
        target_pet.add_task(
            Task(name=task_name, category=category, duration_minutes=int(duration), priority=int(priority))
        )
        st.success(f"Added **{task_name}** to {selected_pet_name}.")

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
    if st.button("Generate schedule", type="primary"):
        for pet in owner.pets:
            if not pet.get_tasks():
                continue
            scheduler = Scheduler(pet)       # inherits owner's time budget automatically
            scheduler.generate_schedule()

            st.subheader(f"📅 {pet.name} ({pet.species})")
            st.code(scheduler.explain_plan(), language=None)

        total_time = sum(t.duration_minutes for t in owner.get_all_tasks())
        budget = owner.get_available_time()
        st.divider()
        if total_time > budget:
            st.warning(
                f"Total task time across all pets ({total_time} min) exceeds your daily budget "
                f"({budget} min). Lower-priority tasks will be skipped."
            )
        else:
            st.success(
                f"All tasks fit within your {budget}-minute daily budget "
                f"(total: {total_time} min)."
            )
