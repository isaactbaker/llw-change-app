# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import select, insert
import numpy as np # Streamlit's new dependency for .explode() may need this

# Import our setup
from database import engine, change_portfolio_table
from logic import TOOLKITS, calculate_triage

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
                "behavioural_barrier": behavioural_barrier # NEW
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

    # --- NEW: Strategic Dashboard Filters ---
    st.subheader("Dashboard Filters")
    col1, col2 = st.columns(2)
    
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

    # Apply filters to create the working DataFrame 'df'
    df = df_full.copy()
    if selected_goal != "All":
        df = df[df['strategic_alignment'] == selected_goal]
    if selected_sponsor != "All":
        df = df[df['exec_sponsor'] == selected_sponsor]

    if df.empty:
        st.warning("No projects match the current filter.")
        return

    # --- Display KPIs (based on filtered data) ---
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Active Projects (Filtered)", len(df))
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
                st.plotly_chart(fig_saturation, use_container_width=True)
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
    col1.plotly_chart(fig_tier, use_container_width=True)
    
    # Chart 3: Projects by Type
    fig_type = px.bar(df, x='change_type', title='Projects by Type (Filtered)', color='change_type')
    col2.plotly_chart(fig_type, use_container_width=True)
    
    st.markdown("---")

    # Chart 4: Project Go-Live Timeline
    st.subheader("Project Go-Live Timeline (Filtered)")
    try:
        df['go_live_date'] = pd.to_datetime(df['go_live_date'])
        fig_timeline = px.timeline(df, x_start="go_live_date", x_end=df["go_live_date"] + pd.Timedelta(days=1), # Show as a point
                                   y="project_name", color="change_tier", title="Project Go-Live Dates")
        fig_timeline.update_yaxes(autorange="reversed") # Show newest at top
        st.plotly_chart(fig_timeline, use_container_width=True)
    except Exception as e:
        st.error(f"Error plotting timeline. Check 'go_live_date' data. Error: {e}")
    
    st.markdown("---")
    
    # Chart 5: Full Project List
    st.subheader("Full Project Portfolio (Filtered)")
    st.dataframe(df) # Display the filtered data in an interactive table

# --- Main App Router (Sidebar) ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Project Intake Form", "PMO Dashboard"])

if page == "Project Intake Form":
    intake_form_page()
else:
    pmo_dashboard_page()