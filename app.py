# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import select, insert, update
import numpy as np
import json

# Import our setup
# --- UPDATED IMPORTS ---
from database import engine, change_portfolio_table, friction_log_table, champion_network_table
from logic import TOOLKITS, calculate_triage
# --- UPDATED AI IMPORT ---
import ai_logic 
# --- END IMPORTS ---

# --- NEW CONSTANT FOR IDEA #3 ---
# This represents the total "effort points" you (as the Change Manager)
# can handle at any one time. This is the 100% mark for the gauge.
TOTAL_CHANGE_CAPACITY = 500 # (e.g., 5 'Full Support' projects)
# --- END NEW CONSTANT ---


# --- App Configuration ---
st.set_page_config(
    page_title="PMO Change Partner",
    layout="wide"
)

# --- 1. The Intake Form Page ---
def intake_form_page():
    st.title("🚀 PMO Change Project Assessment")
    st.markdown("My job is to help you get the right support by running a quick, 15-minute 'Change Impact Assessment.'")

    # Streamlit Forms bundle all inputs and submit at once
    with st.form(key="project_form"):
        st.subheader("1. Project Details")
        col1, col2 = st.columns(2)
        project_name = col1.text_input("Project Name *", key="project_name")
        exec_sponsor = col2.text_input("Executive Sponsor *", key="exec_sponsor")
        go_live_date = col1.date_input("Planned Go-Live Date *", key="go_live_date")
        
        # NEW: Strategic Alignment (for Ben)
        strategic_alignment = col2.selectbox("Primary Strategic Goal *",
            options=[
                "1. Improve Client Outcomes", 
                "2. Increase Operational Efficiency", 
                "3. Enhance Staff Wellbeing/Retention", 
                "4. Regulatory & Compliance",
                "Not Applicable / Other"
            ], key="strategic_alignment")

        st.subheader("2. Human Impact Assessment")
        col1, col2 = st.columns(2)
        
        # NEW: Impacted Departments (for Nicole)
        impacted_departments = col1.multiselect("Impacted Departments / Teams *",
            options=["Frontline Clinical", "AOD Services", "Mental Health", "Corporate (HR/Finance)", "IT", "Leadership", "All Staff"], 
            key="impacted_departments")

        # KEPT: Scale (for scoring)
        scale = col2.selectbox("Impacted Scale (people) *",
                             options=["1-50 people", "50-250 people", "250+ people"], key="scale")

        change_type = col1.selectbox("Change Type *",
                                   options=["Restructure", "New IT System", "AI Bot", "Process Tweak", "Comms Only"], key="change_type")

        impact_depth = col2.selectbox("Impact Depth (daily job) *",
                                    options=["A lot of new skills", "A few new steps", "New login only"], key="impact_depth")
        
        change_history = col1.selectbox("Change History (with this group) *",
                                      options=["Failed before", "First time", "Succeeded before"], key="change_history")
        
        # NEW: Behavioural Barrier (for Dr. Baker)
        behavioural_barrier = col2.selectbox("What is the biggest *human* risk?",
            options=["Capability (They don't know how)", "Motivation (They don't want to / are cynical)", "Opportunity (The system/process is the barrier)"], 
            key="behavioural_barrier")

        st.markdown("---")
        # The submit button
        submitted = st.form_submit_button("Assess & Submit Project")

    # --- Post-Submission Logic ---
    if submitted:
        # Form validation
        if not project_name or not exec_sponsor or not impacted_departments:
            st.error("Please fill in all required fields (*).")
        else:
            # 1. Collect form data
            form_data = {
                "project_name": project_name,
                "exec_sponsor": exec_sponsor,
                "go_live_date": str(go_live_date), # Convert date to string
                "strategic_alignment": strategic_alignment, # NEW
                "impacted_departments": str(impacted_departments), # NEW (store as string list)
                "change_type": change_type,
                "scale": scale, # KEPT for scoring
                "impact_depth": impact_depth,
                "change_history": change_history,
                "behavioural_barrier": behavioural_barrier, # NEW
                # --- NEW FIELD FOR IDEA #2 ---
                "status": "Intake" 
                # --- END NEW FIELD ---
            }

            # 2. Call logic
            triage_results = calculate_triage(form_data)
            form_data.update(triage_results) # Add score and tier to the dict

            # 3. Write to database
            with engine.connect() as conn:
                conn.execute(insert(change_portfolio_table).values(form_data))
                conn.commit()

            # 4. Display results
            st.success(f"Project Submitted! Your project is assessed as: **{triage_results['change_tier']}**")
            st.balloons()
            
            # 5. NEW: Display Dynamic Advice & Toolkit
            st.subheader("Recommended Actions & Toolkit")
            
            if triage_results['change_tier'] == "Full Support":
                st.warning(f"**High Impact Project Identified (Score: {triage_results['impact_score']})**")
                st.markdown(f"This is a **{change_type}** project with a **'{change_history}'** history. This combination creates a high risk of cynicism and fatigue.")
                if behavioural_barrier == "Motivation (They don't want to / are cynical)":
                    st.markdown(f"You correctly identified **Motivation** as the key barrier. Our strategy *must* lead with a 'What's in it for me?' (WIIFM) campaign to rebuild trust.")
                
                st.markdown(TOOLKITS["Full Support"])
                
            elif triage_results['change_tier'] == "Medium Support":
                st.info(f"**Medium Impact Project Identified (Score: {triage_results['impact_score']})**")
                if behavioural_barrier == "Capability (They don't know how)":
                     st.markdown(f"You identified **Capability** as the key barrier. Our focus will be on clear training and manager-led coaching, using the **ADKAR** model.")
                
                st.markdown(TOOLKITS["Medium Support"])
            else:
                st.success(f"**Light Impact Project Identified (Score: {triage_results['impact_score']})**")
                st.markdown("This project primarily requires clear and consistent communication.")
                st.markdown(TOOLKITS["Light Support"])

# --- 2. The PMO Dashboard Page ---
def pmo_dashboard_page():
    st.title("📊 PMO Strategic Portfolio Dashboard")
    
    # Load all data from the database into a Pandas DataFrame
    try:
        df_full = pd.read_sql_table("change_portfolio", engine)
        if df_full.empty:
            st.error("No project data found. Please submit a project on the Intake Form.")
            return
    except Exception as e:
        st.error(f"Failed to load database. Have you updated `database.py`? Error: {e}")
        return

# --- UPDATED: Strategic Dashboard Filters ---
    st.subheader("Dashboard Filters")
    col1, col2, col3 = st.columns(3) 
    
    # Filter by Strategic Goal (for Ben)
    if 'strategic_alignment' in df_full.columns:
        goals = ["All"] + list(df_full['strategic_alignment'].unique())
        selected_goal = col1.selectbox("Filter by Strategic Goal:", options=goals)
    else:
        selected_goal = "All"
        col1.warning("Add 'strategic_alignment' column to DB.")

    # Filter by Sponsor (for Ben & Nicole)
    if 'exec_sponsor' in df_full.columns:
        sponsors = ["All"] + list(df_full['exec_sponsor'].unique())
        selected_sponsor = col2.selectbox("Filter by Executive Sponsor:", options=sponsors)
    else:
        selected_sponsor = "All"
        col2.warning("Add 'exec_sponsor' column to DB.")
        
    # --- NEW FILTER FOR IDEA #2 ---
    if 'status' in df_full.columns:
        # Use a defined list for logical order
        status_options = ["All", "Active", "Intake", "Planning", "Monitoring", "Closed"]
        selected_status = col3.selectbox("Filter by Project Status:", options=status_options)
    else:
        selected_status = "All"
        col3.warning("Add 'status' column to DB.")
    # --- END NEW FILTER ---

    # Apply filters to create the working DataFrame 'df'
    df = df_full.copy()
    if selected_goal != "All":
        df = df[df['strategic_alignment'] == selected_goal]
    if selected_sponsor != "All":
        df = df[df['exec_sponsor'] == selected_sponsor]
    # --- APPLY THE NEW STATUS FILTER ---
    if selected_status != "All":
        df = df[df['status'] == selected_status]
    # --- END ---

    if df.empty:
        st.warning("No projects match the current filter.")
        return


# --- NEW: Capacity Dashboard (Idea #3) ---
    st.markdown("---")
    st.subheader("👩‍💼 Change Manager Capacity")
    
    if 'effort_score' in df.columns:
        # Calculate total effort from the *filtered* dataframe 'df'
        total_effort = df['effort_score'].sum()
        
        # Avoid division by zero if capacity is 0
        if TOTAL_CHANGE_CAPACITY > 0:
            capacity_percentage = total_effort / TOTAL_CHANGE_CAPACITY
        else:
            capacity_percentage = 0
        
        # Make the color change based on capacity
        if capacity_percentage >= 0.9:
            st.error(f"**At Capacity: {int(capacity_percentage * 100)}% Utilized**")
        elif capacity_percentage >= 0.7:
            st.warning(f"**Nearing Capacity: {int(capacity_percentage * 100)}% Utilized**")
        else:
            st.success(f"**Capacity Normal: {int(capacity_percentage * 100)}% Utilized**")

        # The visual progress bar
        st.progress(min(capacity_percentage, 1.0)) # Cap at 100% for the bar
        
        st.metric(
            label=f"Total Effort Points (for Filtered Projects)", 
            value=f"{total_effort} / {TOTAL_CHANGE_CAPACITY}",
            help=f"This sums the effort points for all projects matching the filters above. To see total active workload, set the 'Project Status' filter to 'Active'."
        )

    else:
        st.warning("Could not find 'effort_score' column. Please re-submit a project to populate this data.")
    # --- END NEW: Capacity Dashboard ---

    # --- Display KPIs (based on filtered data) ---
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    # --- METRIC TITLE IS NOW MORE ACCURATE ---
    col1.metric("Projects (Filtered)", len(df)) 
    col2.metric("'Full Support' Projects", len(df[df['change_tier'] == 'Full Support']))
    col3.metric("'Light Support' Projects", len(df[df['change_tier'] == 'Light Support']))
    # --- Display Charts (using filtered 'df') ---
    st.markdown("---")
    
    # --- NEW: Chart 1: Change Saturation Map (Nicole's View) ---
    st.subheader("🔥 Change Saturation Map")
    st.markdown("This map shows which teams are most impacted by the *filtered* change portfolio.")

    if 'impacted_departments' in df.columns:
        try:
            # Clean and 'explode' the list of departments
            all_depts = df['impacted_departments'].apply(lambda x: str(x).strip("[]'").split("', '")).explode()
            # Remove empty/ghost values
            all_depts = all_depts[all_depts != '']
            
            if not all_depts.empty:
                dept_counts = all_depts.value_counts()
                fig_saturation = px.bar(dept_counts, 
                                        x=dept_counts.index, 
                                        y=dept_counts.values,
                                        title="Projects per Department",
                                        labels={'x': 'Department', 'y': 'Number of Active Projects'})
                fig_saturation.update_traces(marker_color='red')
                st.plotly_chart(fig_saturation, use_container_width='stretch')
            else:
                st.info("No departments listed for the projects in this filter.")
        except Exception as e:
            st.error(f"Error processing 'impacted_departments'. Is the data format correct? Error: {e}")
    else:
        st.warning("Add 'impacted_departments' column to your database to enable this chart.")


    st.markdown("---")
    col1, col2 = st.columns(2)
    
    # Chart 2: Projects by Tier
    fig_tier = px.pie(df, names='change_tier', title='Projects by Tier (Filtered)',
                      color_discrete_map={'Light Support':'green', 'Medium Support':'orange', 'Full Support':'red'})
    col1.plotly_chart(fig_tier, use_container_width='stretch')
    
    # Chart 3: Projects by Type
    fig_type = px.bar(df, x='change_type', title='Projects by Type (Filtered)', color='change_type')
    col2.plotly_chart(fig_type, use_container_width='stretch')
    
    st.markdown("---")

    # Chart 4: Project Go-Live Timeline
    st.subheader("Project Go-Live Timeline (Filtered)")
    try:
        df['go_live_date'] = pd.to_datetime(df['go_live_date'])
        fig_timeline = px.timeline(df, x_start="go_live_date", x_end=df["go_live_date"] + pd.Timedelta(days=1), # Show as a point
                                   y="project_name", color="change_tier", title="Project Go-Live Dates")
        fig_timeline.update_yaxes(autorange="reversed") # Show newest at top
        st.plotly_chart(fig_timeline, use_container_width='stretch')
    except Exception as e:
        st.error(f"Error plotting timeline. Check 'go_live_date' data. Error: {e}")
    
    st.markdown("---")
    
    # Chart 5: Full Project List
    st.subheader("Full Project Portfolio (Filtered)")
    st.dataframe(df) # Display the filtered data in an interactive table



# --- 3. The Project "Drill-Down" Page (REBUILT with Tabs) ---
def project_detail_page():
    st.title("🔎 Project Details & Workbench")
    st.markdown("Select a project to view its details and update its status.")

    # --- (This part is unchanged) ---
    # Load all project names for the selector
    try:
        with engine.connect() as conn:
            projects = conn.execute(select(
                change_portfolio_table.c.id, 
                change_portfolio_table.c.project_name
            )).fetchall()
        
        if not projects:
            st.warning("No projects found. Please submit one via the Intake Form.")
            return
        
        project_map = {project.project_name: project.id for project in projects}
        project_names = ["Select a project..."] + list(project_map.keys())
        selected_project_name = st.selectbox("Select Project:", options=project_names)

    except Exception as e:
        st.error(f"Error loading projects: {e}")
        return

    # --- Once a project is selected, show its details ---
    if selected_project_name != "Select a project...":
        project_id = project_map[selected_project_name]

        # 1. Get the project's data
        with engine.connect() as conn:
            stmt = select(change_portfolio_table).where(change_portfolio_table.c.id == project_id)
            project_data = conn.execute(stmt).fetchone() 
            
            if not project_data:
                st.error("Project not found.")
                return

        # 2. Display the data (unchanged)
        st.subheader(f"Project: {project_data.project_name}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Change Tier", project_data.change_tier)
        col2.metric("Impact Score", project_data.impact_score)
        col3.metric("Go-Live Date", str(project_data.go_live_date))
        col4.metric("Executive Sponsor", project_data.exec_sponsor)
        st.markdown("---")

        # 3. Change Manager Workbench (unchanged)
        st.subheader("Change Manager Workbench")
        status_options = ["Intake", "Planning", "Active", "Monitoring", "Closed"]
        current_status = project_data.status
        current_status_index = status_options.index(current_status) if current_status in status_options else 0
        
        new_status = st.selectbox(
            "Update Project Status:",
            options=status_options,
            index=current_status_index
        )

        if st.button("Save Status Update"):
            try:
                with engine.connect() as conn:
                    update_stmt = update(change_portfolio_table).where(
                        change_portfolio_table.c.id == project_id
                    ).values(status=new_status)
                    conn.execute(update_stmt)
                    conn.commit()
                st.success(f"Status updated to **{new_status}**!")
                st.rerun() 
            except Exception as e:
                st.error(f"Failed to update status: {e}")
        
        st.markdown("---")

        # --- NEW: Create Tabs for Playbook and Diagnostic ---
        tab_playbook, tab_diagnostic = st.tabs([
            "📖 Interactive Playbook", 
            "🚀 Readiness Diagnostic"
        ])

        # --- Tab 1: Interactive Playbook (Your existing code) ---
        with tab_playbook:
            st.subheader("Interactive Change Playbook")
            try:
                playbook_json = project_data.playbook_data
                if playbook_json:
                    playbook_list = json.loads(playbook_json)
                else:
                    playbook_list = [] 

                playbook_df = pd.DataFrame(playbook_list)

                edited_df = st.data_editor(
                    playbook_df,
                    column_config={
                        "Status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["To Do", "In Progress", "Done"],
                            required=True,
                        ),
                        "Category": st.column_config.TextColumn(width="medium"),
                        "Task": st.column_config.TextColumn(width="large"),
                    },
                    hide_index=True,
                    num_rows="dynamic"
                )

                if st.button("Save Playbook Updates"):
                    updated_playbook_json = edited_df.to_json(orient="records")
                    with engine.connect() as conn:
                        update_stmt = update(change_portfolio_table).where(
                            change_portfolio_table.c.id == project_id
                        ).values(playbook_data=updated_playbook_json)
                        conn.execute(update_stmt)
                        conn.commit()
                    st.success("Playbook updated successfully!")
                    st.rerun()

            except Exception as e:
                st.error(f"Error loading playbook: {e}")
                st.info("Note: Projects submitted before this feature was added may not have a playbook.")

        # --- Tab 2: Readiness Diagnostic (NEW FEATURE) ---
        with tab_diagnostic:
            st.subheader("Behavioral Readiness Diagnostic (COM-B)")

            # Logic Gate: Only show for Medium/Full support projects
            if project_data.change_tier == "Light Support":
                st.info("This project is 'Light Support'. A full behavioral diagnostic is not required.")
                st.markdown("This tool is designed for Medium and Full Support projects where identifying specific behavioral barriers (Capability, Opportunity, Motivation) is critical.")
            else:
                # Show saved plan first
                if project_data.readiness_plan_html:
                    st.subheader("Saved Intervention Plan")
                    st.markdown(project_data.readiness_plan_html, unsafe_allow_html=True)
                    st.markdown("---")
                    st.info("To generate a new plan, fill out the form below. Saving will overwrite the plan above.")

                # The 10-Min Input Form
                st.subheader("Generate New Intervention Plan")
                
                # Use a consistent list of departments
                dept_options = ["Frontline Clinical", "AOD Services", "Mental Health", "Corporate (HR/Finance)", "IT", "Leadership", "All Staff"]

                with st.form("readiness_form"):
                    low_groups = st.multiselect(
                        "Which groups show low readiness? *", 
                        options=dept_options
                    )
                    barrier = st.selectbox(
                        "What is the primary *barrier* you observe? (COM-B) *", 
                        options=[
                            "Capability (They don't know how)", 
                            "Opportunity (The system/process is the barrier)", 
                            "Motivation (They don't want to / are cynical)"
                        ]
                    )
                    rumor = st.text_area(
                        "What is the main 'rumor' or 'story' you are hearing? *", 
                        placeholder="e.g., 'This is just another cost-cutting exercise' or 'This will double our admin work.'"
                    )
                    
                    submitted = st.form_submit_button("Generate Intervention Plan")

                if submitted:
                    if not low_groups or not barrier or not rumor:
                        st.error("Please fill in all required fields (*).")
                    else:
                        with st.spinner("🤖 Dr. Baker is diagnosing... Generating behavioral plan..."):
                            report = ai_logic.run_readiness_diagnostic(
                                project_name=project_data.project_name,
                                low_readiness_groups=low_groups,
                                barrier=barrier,
                                rumor=rumor
                            )
                            # Save to session state to display it
                            st.session_state[f'readiness_report_{project_id}'] = report
                
                # Display the generated report from session state
                report_key = f'readiness_report_{project_id}'
                if report_key in st.session_state:
                    st.markdown("---")
                    st.subheader("Generated AI Plan")
                    
                    generated_report = st.session_state[report_key]
                    st.markdown(generated_report)
                    
                    # Add the "Save Plan" button
                    if st.button("Save This Plan to the Project"):
                        try:
                            with engine.connect() as conn:
                                update_stmt = update(change_portfolio_table).where(
                                    change_portfolio_table.c.id == project_id
                                ).values(
                                    readiness_plan_html=generated_report
                                )
                                conn.execute(update_stmt)
                                conn.commit()
                            st.success("Intervention plan saved successfully!")
                            # Clear the session state key after saving
                            del st.session_state[report_key]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save plan: {e}")


# --- 4. The "My Workbench" Page (REBUILT for Idea #5 + AI Analyst) ---
def my_workbench_page():
    st.title("👩‍💼 My Change Workbench")
    st.markdown("Your personal cockpit for all active projects, tasks, and AI analysis.")

    # --- Load all portfolio data ---
    try:
        df_projects = pd.read_sql_table("change_portfolio", engine)
        if df_projects.empty:
            st.error("No project data found. Please submit a project on the Intake Form.")
            return
        
        # Get a list of "Active" project names for dropdowns
        active_project_names = df_projects[df_projects['status'] == 'Active']['project_name'].tolist()

    except Exception as e:
        st.error(f"Failed to load project database. Error: {e}")
        return

    # --- Create Tabs for the Workbench ---
    tab_tasks, tab_friction, tab_survey = st.tabs([
        "My Priority Tasks", 
        "🔥 Friction & Sludge Log", 
        "📊 Survey AI Analyst"
    ])

    # --- Tab 1: My Priority Tasks (Your existing Idea #5) ---
    with tab_tasks:
        st.subheader("My Priority Tasks (To Do / In Progress)")
        
        df_active = df_projects[df_projects['status'] == 'Active'].copy()
        
        if df_active.empty:
            st.info("You have no 'Active' projects. No tasks to show.")
        else:
            all_tasks = []
            for index, project in df_active.iterrows():
                project_name = project['project_name']
                playbook_json = project['playbook_data']
                if playbook_json:
                    try:
                        playbook_list = json.loads(playbook_json)
                        for task in playbook_list:
                            if task['Status'] != 'Done':
                                all_tasks.append({
                                    "Project": project_name,
                                    "Category": task['Category'],
                                    "Task": task['Task'],
                                    "Status": task['Status']
                                })
                    except Exception as e:
                        st.warning(f"Could not parse playbook for {project_name}.")
            
            if not all_tasks:
                st.success("You have no outstanding tasks on active projects. All done! 🎉")
            else:
                tasks_df = pd.DataFrame(all_tasks)
                st.dataframe(tasks_df, use_container_width='stretch')
                st.markdown(f"**You have {len(tasks_df)} total priority tasks.**")
                st.info("To edit a task, go to the 'Project Details' page.")

    # --- Tab 2: Friction & Sludge Log ---
    with tab_friction:
        st.subheader("Log & Analyze Change Friction")
        
        # 1. The Form to log new friction
        with st.form("friction_form"):
            st.markdown("Heard a complaint? Saw a broken link? Log it here.")
            # Select from active projects, or allow "General"
            project = st.selectbox("Related Project", options=["General"] + active_project_names)
            note = st.text_area("Friction Note", placeholder="e.g., 'A nurse told me the new login button is hidden and takes 6 clicks.'")
            submitted = st.form_submit_button("Log Friction Note")
            
            if submitted:
                if not note:
                    st.error("Please enter a friction note.")
                else:
                    # Write to the new friction_log_table
                    new_log = {"project_name": project, "friction_note": note}
                    with engine.connect() as conn:
                        conn.execute(insert(friction_log_table).values(new_log))
                        conn.commit()
                    st.success("Friction logged!")
        
        st.markdown("---")
        
        # 2. Display and Analyze existing logs
        try:
            df_friction = pd.read_sql_table("friction_log", engine)
            st.subheader(f"Current Friction Log ({len(df_friction)} entries)")
            st.dataframe(df_friction[['project_name', 'friction_note', 'status', 'logged_date']], use_container_width='stretch')

            if not df_friction.empty and st.button("Run AI Friction Analysis (All Entries)"):
                with st.spinner("🤖 AI Analyst is reading all friction notes..."):
                    analysis_report = ai_logic.run_friction_analysis(df_friction)
                    st.markdown(analysis_report)

        except Exception as e:
            st.error(f"Failed to load friction log. Error: {e}")

    # --- Tab 3: Survey AI Analyst ---
    with tab_survey:
        st.subheader("Analyze Survey Comments")
        st.markdown("Upload a CSV/Excel file with open-ended survey comments.")
        
        uploaded_file = st.file_uploader("Upload Survey Data", type=["csv", "xlsx"])
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_survey = pd.read_csv(uploaded_file)
                else:
                    df_survey = pd.read_excel(uploaded_file)
                

                st.dataframe(df_survey.head())
                # You can add a caption *outside* the dataframe like this:
                st.caption("Showing first 5 rows of your data.")
                                
                # Get column to analyze
                col_name = st.text_input("Which column has the comments you want to analyze?", 
                                         help="e.g., 'Q5 Comments', 'Additional Feedback'")
                
                if st.button(f"Run AI Analysis on column: '{col_name}'"):
                    if not col_name:
                        st.error("Please enter a column name.")
                    else:
                        with st.spinner("🤖 AI Analyst is reading thousands of comments..."):
                            analysis_report = ai_logic.run_survey_analysis(df_survey, col_name)
                            st.markdown(analysis_report)
            
            except Exception as e:
                st.error(f"Failed to process file: {e}")




# --- 5. The "Champion Network" Page (CORRECTED VERSION) ---
def champion_network_page():
    st.title("👥 Change Champion Network")
    st.markdown("Manage your network of champions and use the AI Co-pilot to scale your engagement.")

    # --- Load all project names for dropdowns ---
    try:
        df_projects = pd.read_sql_table("change_portfolio", engine)
        if df_projects.empty:
            st.warning("No projects found. Please submit a project first.")
            project_names = []
            project_data_map = {}
        else:
            project_names = df_projects['project_name'].tolist()
            # Create a dictionary to look up project data by name
            project_data_map = df_projects.set_index('project_name').to_dict('index')
            
    except Exception as e:
        st.error(f"Failed to load project database. Error: {e}")
        return

    # --- Create Tabs for this page ---
    tab_manage, tab_copilot = st.tabs(["Manage Network", "AI Co-pilot"])

    # --- Tab 1: Manage Champion Network (Unchanged) ---
    with tab_manage:
        st.subheader("Add a New Champion")
        
        dept_options = ["Frontline Clinical", "AOD Services", "Mental Health", "Corporate (HR/Finance)", "IT", "Leadership", "All Staff"]

        with st.form("add_champion_form"):
            name = st.text_input("Champion Name")
            email = st.text_input("Champion Email")
            dept = st.selectbox("Department", options=dept_options)
            project = st.selectbox("Assigned Project", options=project_names)
            
            submitted = st.form_submit_button("Add Champion")
            
            if submitted:
                if not name or not project:
                    st.error("Please provide at least a name and assigned project.")
                else:
                    new_champion = {
                        "champion_name": name,
                        "champion_email": email,
                        "department": dept,
                        "project_name": project
                    }
                    with engine.connect() as conn:
                        conn.execute(insert(champion_network_table).values(new_champion))
                        conn.commit()
                    st.success(f"Added {name} to the network for {project}!")

        st.markdown("---")
        
        st.subheader("Current Champion Network")
        try:
            df_champions = pd.read_sql_table("champion_network", engine)
            if df_champions.empty:
                st.info("No champions have been added yet.")
            else:
                st.dataframe(df_champions, width='stretch') # <-- Already includes the 'width' fix
        except Exception as e:
            st.error(f"Failed to load champion network. Error: {e}")

    # --- Tab 2: AI Co-pilot (CORRECTED LOGIC) ---
    with tab_copilot:
        st.subheader("Generate Champion Communications")
        st.markdown("Select a project to generate context-aware communications for your champions.")

        if not project_names:
            st.warning("No projects available to generate comms.")
            return

        selected_project = st.selectbox("Select Project for Comms", options=project_names)
        
        if selected_project:
            project_context = project_data_map.get(selected_project)
            
            if not project_context:
                st.error("Could not load project context.")
                return

            st.markdown(f"**Project Context:** Tier is `{project_context['change_tier']}` and main barrier is `{project_context['behavioural_barrier']}`.")

            col1, col2 = st.columns(2)
            
            # --- DEFINE A DYNAMIC SESSION STATE KEY ---
            report_key = f'champion_report_{selected_project}'

            # Button 1: Kick-off Email
            if col1.button("Generate Kick-off Email"):
                with st.spinner("🤖 Co-pilot is drafting the email..."):
                    email_draft = ai_logic.run_champion_kickoff_email(selected_project)
                    st.session_state[report_key] = email_draft # <-- Use dynamic key

            # Button 2: Talking Points
            if col2.button("Generate Talking Points Brief"):
                with st.spinner("🤖 Co-pilot is creating the brief..."):
                    brief_draft = ai_logic.run_champion_talking_points(
                        project_name=selected_project,
                        change_tier=project_context['change_tier'],
                        behavioural_barrier=project_context['behavioural_barrier']
                    )
                    st.session_state[report_key] = brief_draft # <-- Use dynamic key

            # Display the result
            if report_key in st.session_state:
                st.markdown("---")
                st.subheader("AI Co-pilot Draft")
                st.text_area("You can edit and copy the text below:", 
                             value=st.session_state[report_key], 
                             height=400)

# --- 6. The "Comms Campaign Director" Page (NEW) ---
def comms_campaign_page():
    st.title("📣 Comms Campaign Director")
    st.markdown("Design a multi-phase, behavioral communications campaign for any project.")

    # --- Load all project names and context ---
    try:
        df_projects = pd.read_sql_table("change_portfolio", engine)
        if df_projects.empty:
            st.warning("No projects found. Please submit a project first.")
            project_names = []
            project_data_map = {}
        else:
            project_names = ["Select a project..."] + df_projects['project_name'].tolist()
            # Create a dictionary to look up project data by name
            project_data_map = df_projects.set_index('project_name').to_dict('index')
            
    except Exception as e:
        st.error(f"Failed to load project database. Error: {e}")
        return

    # --- The 10-Min Input Form ---
    with st.form("comms_campaign_form"):
        st.subheader("Campaign Inputs")
        
        selected_project = st.selectbox(
            "Which project is this campaign for? *", 
            options=project_names
        )
        
        audience_segments = st.multiselect(
            "Select your audience segments: *", 
            options=["Enthusiasts", "Skeptics", "Fence-Sitters", "Impacted Managers", "Frontline Staff", "Leadership"]
        )
        
        narrative = st.text_input(
            "What is the single most important message (Master Narrative)? *", 
            placeholder="e.g., 'This frees up our clinicians to spend more time with clients.'"
        )
        
        tough_question = st.text_area(
            "What is the biggest 'tough question' you expect? *", 
            placeholder="e.g., 'Is this going to automate my job?' or 'Why are we doing this now?'"
        )
        
        submitted = st.form_submit_button("Generate Behavioral Comms Campaign")

    # --- Form Submission & AI Call ---
    if submitted:
        if selected_project == "Select a project..." or not audience_segments or not narrative or not tough_question:
            st.error("Please fill in all required fields (*).")
        else:
            with st.spinner("🤖 The Comms Director is drafting your campaign..."):
                campaign_report = ai_logic.run_comms_campaign_generator(
                    project_name=selected_project,
                    audience_segments=audience_segments,
                    narrative=narrative,
                    tough_question=tough_question
                )
                # Save to session state to display
                st.session_state[f'comms_report_{selected_project}'] = campaign_report

    # --- Display the Generated Report ---
    report_key = f'comms_report_{selected_project}'
    if report_key in st.session_state:
        st.markdown("---")
        st.subheader("Generated AI Campaign Blueprint")
        
        generated_report = st.session_state[report_key]
        st.markdown(generated_report)
        
        # Add the "Save Plan" button
        if st.button("Save This Campaign to the Project"):
            try:
                # Get the project ID from the name
                project_id = project_data_map[selected_project]['id']
                
                with engine.connect() as conn:
                    update_stmt = update(change_portfolio_table).where(
                        change_portfolio_table.c.id == project_id
                    ).values(
                        comms_campaign_html=generated_report
                    )
                    conn.execute(update_stmt)
                    conn.commit()
                st.success(f"Campaign saved to '{selected_project}' successfully!")
                # Clear the session state key after saving
                del st.session_state[report_key]
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save plan: {e}")

    # --- Show Saved Plan (if one exists) ---
    if selected_project != "Select a project...":
        project_data = project_data_map.get(selected_project)
        if project_data and project_data.get('comms_campaign_html'):
            st.markdown("---")
            st.subheader(f"Saved Campaign Plan for '{selected_project}'")
            st.markdown(project_data['comms_campaign_html'], unsafe_allow_html=True)




# --- Main App Router (Sidebar) ---
st.sidebar.title("Navigation")
# --- UPDATED LIST ---
page = st.sidebar.radio("Go to:", [
    "My Workbench",
    "PMO Dashboard", 
    "Project Details",
    "Champion Network",
    "📣 Comms Campaign Director", # <--- NEW
    "Project Intake Form"
])

if page == "Project Intake Form":
    intake_form_page()
elif page == "PMO Dashboard":
    pmo_dashboard_page()
elif page == "Project Details":
    project_detail_page()
elif page == "My Workbench":
    my_workbench_page()
elif page == "Champion Network":
    champion_network_page()
# --- NEW PAGE ROUTE ---
elif page == "📣 Comms Campaign Director":
    comms_campaign_page()
# --- END NEW PAGE ---