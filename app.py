# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import select, insert, update
import numpy as np
import json
import datetime

# Import our setup
# --- UPDATED IMPORTS ---
from database import engine, change_portfolio_table, friction_log_table, champion_network_table, health_snapshot_table # <-- ADDED
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


# --- NEW: Portfolio Change Health (PHASE 3 DELIVERABLE) ---
    st.markdown("---")
    st.subheader("📈 Portfolio Change Health (Latest Snapshots)")
    st.markdown("This dashboard shows the latest health metrics for all **filtered** projects.")

    try:
        df_health_full = pd.read_sql_table("health_snapshot", engine)
        if df_health_full.empty:
            st.info("No health snapshots have been logged yet. Data will appear here once you log it on the 'Project Details' page.")
        else:
            # Get the single latest snapshot for EACH project
            df_latest_health = df_health_full.sort_values('log_date').groupby('project_id').last().reset_index()
            
            # Merge with the filtered project list 'df'
            # This ensures we only show health for "Active" projects (or whatever the filter is)
            df_health_merged = pd.merge(
                df, 
                df_latest_health, 
                left_on='id', 
                right_on='project_id', 
                how='inner'
            )

            if df_health_merged.empty:
                st.warning("No projects in your current filter (e.g., 'Active') have any health snapshots logged.")
            else:
                # 1. Display KPIs (for Ben)
                col1, col2, col3 = st.columns(3)
                col1.metric(
                    f"Avg. Readiness (Filtered)", 
                    f"{df_health_merged['readiness_score'].mean():.1f} / 5"
                )
                col2.metric(
                    f"Avg. Adoption Rate (Filtered)", 
                    f"{df_health_merged['adoption_rate_pct'].mean():.0f}%"
                )
                col3.metric(
                    f"Avg. Manager Confidence (Filtered)", 
                    f"{df_health_merged['manager_confidence'].mean():.1f} / 5"
                )
                
                # 2. Display Bubble Chart (for Ben)
                fig_health = px.scatter(
                    df_health_merged,
                    x='readiness_score',
                    y='adoption_rate_pct',
                    size='effort_score',
                    color='change_tier',
                    hover_name='project_name',
                    title='Project Health: Readiness vs. Adoption',
                    labels={
                        'readiness_score': 'Readiness Score (1-5)',
                        'adoption_rate_pct': 'Adoption Rate (%)'
                    },
                    color_discrete_map={'Light Support':'green', 'Medium Support':'orange', 'Full Support':'red'}
                )
                fig_health.update_layout(xaxis=dict(range=[0.5, 5.5]), yaxis=dict(range=[-5, 105]))
                st.plotly_chart(fig_health, width='stretch')
    except Exception as e:
        st.error(f"Error loading Health Dashboard: {e}")
    # --- END NEW HEALTH DASHBOARD ---



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
# --- 3. The Project "Drill-Down" Page (REBUILT with Health Tab) ---
def project_detail_page():
    st.title("🔎 Project Details & Workbench")
    st.markdown("Select a project to view its details and update its status.")

    # --- (Load project selector - unchanged) ---
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

        # 1. Get the project's data (unchanged)
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

        # --- TABS ARE UPDATED TO INCLUDE 'CHANGE HEALTH' ---
        tab_playbook, tab_diagnostic, tab_health = st.tabs([
            "📖 Interactive Playbook", 
            "🚀 Readiness Diagnostic",
            "📈 Change Health" # <-- NEW TAB
        ])

        # --- Tab 1: Interactive Playbook (unchanged) ---
        with tab_playbook:
            st.subheader("Interactive Change Playbook")
            # ... (all your existing playbook code, no changes) ...
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
                            "Status", options=["To Do", "In Progress", "Done"], required=True,
                        ),
                        "Category": st.column_config.TextColumn(width="medium"),
                        "Task": st.column_config.TextColumn(width="large"),
                    },
                    hide_index=True, num_rows="dynamic"
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

        # --- Tab 2: Readiness Diagnostic (unchanged) ---
        with tab_diagnostic:
            st.subheader("Behavioral Readiness Diagnostic (COM-B)")
            # ... (all your existing readiness diagnostic code, no changes) ...
            if project_data.change_tier == "Light Support":
                st.info("This project is 'Light Support'. A full behavioral diagnostic is not required.")
            else:
                if project_data.readiness_plan_html:
                    st.subheader("Saved Intervention Plan")
                    st.markdown(project_data.readiness_plan_html, unsafe_allow_html=True)
                    st.markdown("---")
                
                st.subheader("Generate New Intervention Plan")
                dept_options = ["Frontline Clinical", "AOD Services", "Mental Health", "Corporate (HR/Finance)", "IT", "Leadership", "All Staff"]
                with st.form("readiness_form"):
                    low_groups = st.multiselect("Which groups show low readiness? *", options=dept_options)
                    barrier = st.selectbox("What is the primary *barrier*? (COM-B) *", options=["Capability (They don't know how)", "Opportunity (The system/process is the barrier)", "Motivation (They don't want to / are cynical)"])
                    rumor = st.text_area("What is the main 'rumor' or 'story'? *", placeholder="e.g., 'This is just another cost-cutting exercise'...")
                    submitted = st.form_submit_button("Generate Intervention Plan")

                if submitted:
                    if not low_groups or not barrier or not rumor:
                        st.error("Please fill in all required fields (*).")
                    else:
                        with st.spinner("🤖 Dr. Baker is diagnosing..."):
                            report = ai_logic.run_readiness_diagnostic(project_name=project_data.project_name, low_readiness_groups=low_groups, barrier=barrier, rumor=rumor)
                            st.session_state[f'readiness_report_{project_id}'] = report
                
                report_key = f'readiness_report_{project_id}'
                if report_key in st.session_state:
                    st.markdown("---")
                    st.subheader("Generated AI Plan")
                    generated_report = st.session_state[report_key]
                    st.markdown(generated_report)
                    if st.button("Save This Plan to the Project"):
                        try:
                            with engine.connect() as conn:
                                update_stmt = update(change_portfolio_table).where(change_portfolio_table.c.id == project_id).values(readiness_plan_html=generated_report)
                                conn.execute(update_stmt)
                                conn.commit()
                            st.success("Intervention plan saved successfully!")
                            del st.session_state[report_key]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save plan: {e}")

        # --- TAB 3: CHANGE HEALTH (NEW FEATURE) ---
        with tab_health:
            st.subheader("Project Health Dashboard")
            st.markdown("Log and track the lead (PMO) and lag (ROI) indicators for this project over time.")

            # --- Part A: Visualization ---
            try:
                df_health_full = pd.read_sql_table("health_snapshot", engine)
                df_project_health = df_health_full[df_health_full['project_id'] == project_data.id].copy()

                if df_project_health.empty:
                    st.info("No health snapshots logged for this project yet. Use the form below to add one.")
                else:
                    # 1. Show Latest KPIs
                    df_project_health['log_date'] = pd.to_datetime(df_project_health['log_date'])
                    df_project_health = df_project_health.sort_values(by="log_date")
                    latest_snapshot = df_project_health.iloc[-1]
                    
                    st.subheader("Latest Snapshot")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Adoption Rate", f"{latest_snapshot['adoption_rate_pct']}%")
                    col2.metric("Readiness Score", f"{latest_snapshot['readiness_score']} / 5")
                    col3.metric("Sentiment Score", f"{latest_snapshot['sentiment_score']} / 5")

                    # 2. Show Line Chart (PMO View)
                    st.subheader("Lead Indicators Over Time (PMO View)")
                    df_chart_data = df_project_health.set_index('log_date')[['readiness_score', 'sentiment_score', 'manager_confidence']]
                    st.line_chart(df_chart_data)

            except Exception as e:
                st.error(f"Error loading health data: {e}")

            # --- Part B: Input Form ---
            st.markdown("---")
            st.subheader("Log New Health Snapshot")
            with st.form("health_snapshot_form"):
                log_date_input = st.date_input("Log Date", datetime.date.today())
                
                st.subheader("Lead Indicators (1-5 Scale)")
                readiness = st.slider("Overall Readiness (1=Low, 5=High)", 1, 5, 3)
                sentiment = st.slider("Staff Sentiment (1=Negative, 5=Positive)", 1, 5, 3)
                manager = st.slider("Manager Confidence (1=Low, 5=High)", 1, 5, 3)
                
                st.subheader("Lag Indicators (ROI)")
                adoption = st.number_input("Adoption Rate (%)", 0, 100, 0)
                behavior = st.number_input("Behavior Adoption (%)", 0, 100, 0)
                turnover = st.number_input("Staff Turnover (%) (This Period)", 0, 100, 0)
                
                notes = st.text_area("Notes", placeholder="e.g., 'Sentiment is low due to login bugs. Adoption is at 20% but rising.'")
                
                submitted = st.form_submit_button("Log Health Snapshot")

                if submitted:
                    try:
                        new_snapshot = {
                            "project_id": project_data.id,
                            "log_date": str(log_date_input),
                            "readiness_score": readiness,
                            "sentiment_score": sentiment,
                            "manager_confidence": manager,
                            "adoption_rate_pct": adoption,
                            "behavior_adoption_pct": behavior,
                            "staff_turnover_pct": turnover,
                            "notes": notes
                        }
                        with engine.connect() as conn:
                            conn.execute(insert(health_snapshot_table).values(new_snapshot))
                            conn.commit()
                        st.success("Health snapshot logged successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error logging snapshot: {e}")



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






# --- 7. The "Manager Co-pilot" Page (NEW) ---
def manager_copilot_page():
    st.title("🧑‍💼 Manager Co-pilot")
    st.markdown("Your 'just-in-time' tool for handling tough, change-related conversations.")
    st.markdown("---")

    # Load project names for context
    try:
        df_projects = pd.read_sql_table("change_portfolio", engine)
        project_names = ["Not project-specific"] + df_projects['project_name'].tolist()
    except Exception as e:
        st.error("Could not load projects. Defaulting to general topics.")
        project_names = ["Not project-specific"]

    # 1. Select the Tool
    tool_choice = st.selectbox(
        "What do you need help with?",
        [
            "Select a tool...",
            "Supporting a Burned-Out Team Member",
            "Having a Crucial Conversation",
            "Handling Resistance (OARS Model)"
        ]
    )

    # --- Add logic to clear old output when tool changes ---
    if 'current_tool_choice' not in st.session_state:
        st.session_state['current_tool_choice'] = tool_choice
    
    if st.session_state['current_tool_choice'] != tool_choice:
        if 'manager_guide' in st.session_state:
            del st.session_state['manager_guide']
        st.session_state['current_tool_choice'] = tool_choice
    # --- End of clearing logic ---

    context = {}
    run_button = False

    # 2. Show Dynamic Form based on Tool Choice
    if tool_choice == "Supporting a Burned-Out Team Member":
        context["behavior"] = st.text_input(
            "What behavior are you observing? *",
            placeholder="e.g., 'They are quiet in meetings and missing small deadlines.'"
        )
        run_button = st.button("Generate Support Script")
        
    elif tool_choice == "Having a Crucial Conversation":
        context["topic"] = st.text_input(
            "What is the specific topic? *",
            placeholder="e.g., 'Not following the new process' or 'Negative attitude in team meetings'"
        )
        context["emotion"] = st.text_input(
            "How is the employee likely feeling? *",
            placeholder="e.g., 'Anxious' or 'Angry' or 'Defensive'"
        )
        run_button = st.button("Generate Conversation Starter")

    elif tool_choice == "Handling Resistance (OARS Model)":
        context["project_name"] = st.selectbox(
            "Which project are they resisting? *",
            options=project_names
        )
        context["resistance_statement"] = st.text_area(
            "What are they saying? *",
            placeholder="e.g., 'This is just a waste of time, the old way was faster.' or 'Why do we have to change again?'"
        )
        run_button = st.button("Generate OARS Guide & Script")

    # 3. Run AI and display output
    if run_button:
        # Simple validation
        if not all(context.values()):
            st.error("Please fill in all the fields for this tool.")
        else:
            with st.spinner("🤖 Co-pilot is generating your guide..."):
                generated_guide = ai_logic.run_manager_copilot(tool_choice, context)
                st.session_state['manager_guide'] = generated_guide
    
    if 'manager_guide' in st.session_state and tool_choice != "Select a tool...":
        st.markdown("---")
        st.subheader("Your AI-Generated Guide & Script")
        st.markdown(st.session_state['manager_guide'])
        st.info("You can copy this text, adapt it to your own voice, and use it in your next conversation.")

# --- END NEW FUNCTION ---








# --- Main App Router (Sidebar) ---
st.sidebar.title("Navigation")
# --- UPDATED LIST ---
page = st.sidebar.radio("Go to:", [
    "My Workbench",
    "PMO Dashboard", 
    "Project Details",
    "Champion Network",
    "📣 Comms Campaign Director",
    "🧑‍💼 Manager Co-pilot", 
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
elif page == "📣 Comms Campaign Director":
    comms_campaign_page()
# --- NEW PAGE ROUTE ---
elif page == "🧑‍💼 Manager Co-pilot":
    manager_copilot_page()
# --- END NEW PAGE ---