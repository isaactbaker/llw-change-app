# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import select, insert

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
    st.markdown("My job is to help you get the right support by running a quick 'Change Impact Assessment.'")

    # Streamlit Forms bundle all inputs and submit at once
    with st.form(key="project_form"):
        st.subheader("Project Details")
        project_name = st.text_input("Project Name *", key="project_name")
        exec_sponsor = st.text_input("Executive Sponsor *", key="exec_sponsor")
        go_live_date = st.date_input("Planned Go-Live Date *", key="go_live_date")

        st.subheader("Impact Assessment")
        change_type = st.selectbox("Change Type *",
                                   options=["Restructure", "New IT System", "AI Bot", "Process Tweak", "Comms Only"], key="change_type")
        scale = st.selectbox("Impacted Scale (people) *",
                             options=["1-50 people", "50-250 people", "250+ people"], key="scale")
        impact_depth = st.selectbox("Impact Depth (daily job) *",
                                    options=["A lot of new skills", "A few new steps", "New login only"], key="impact_depth")
        change_history = st.selectbox("Change History (with this group) *",
                                      options=["Failed before", "First time", "Succeeded before"], key="change_history")

        # The submit button
        submitted = st.form_submit_button("Assess & Submit Project")

    # --- Post-Submission Logic ---
    if submitted:
        if not project_name or not exec_sponsor:
            st.error("Please fill in all required fields.")
        else:
            # 1. Collect form data
            form_data = {
                "project_name": project_name,
                "exec_sponsor": exec_sponsor,
                "go_live_date": str(go_live_date), # Convert date to string
                "change_type": change_type,
                "scale": scale,
                "impact_depth": impact_depth,
                "change_history": change_history
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
            
            # 5. Display the correct toolkit
            st.markdown(TOOLKITS[triage_results['change_tier']])

# --- 2. The PMO Dashboard Page ---
def pmo_dashboard_page():
    st.title("📊 PMO Change Saturation Map")
    
    # Load all data from the database into a Pandas DataFrame
    try:
        df = pd.read_sql_table("change_portfolio", engine)
    except:
        st.error("No project data found.")
        return

    # --- Display KPIs ---
    col1, col2 = st.columns(2)
    col1.metric("Total Active Projects", len(df))
    col2.metric("'Full Support' Projects", len(df[df['change_tier'] == 'Full Support']))

    st.markdown("---")

    # --- Display Charts (using Plotly Express) ---
    col1, col2 = st.columns(2)
    
    # Chart 1: Projects by Tier
    fig_tier = px.pie(df, names='change_tier', title='Projects by Tier',
                      color_discrete_map={'Light Support':'green', 'Medium Support':'orange', 'Full Support':'red'})
    col1.plotly_chart(fig_tier, use_container_width=True)
    
    # Chart 2: Projects by Type
    fig_type = px.bar(df, x='change_type', title='Projects by Type', color='change_type')
    col2.plotly_chart(fig_type, use_container_width=True)
    
    st.markdown("---")

    # Chart 3: Project Go-Live Timeline
    # Note: Requires converting go_live_date back to datetime
    df['go_live_date'] = pd.to_datetime(df['go_live_date'])
    fig_timeline = px.timeline(df, x_start="go_live_date", x_end=df["go_live_date"] + pd.Timedelta(days=1), # Show as a point
                               y="project_name", color="change_tier", title="Project Go-Live Dates")
    fig_timeline.update_yaxes(autorange="reversed") # Show newest at top
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.markdown("---")
    
    # Chart 4: Full Project List
    st.subheader("Full Project Portfolio")
    st.dataframe(df) # Display the raw data in an interactive table

# --- Main App Router (Sidebar) ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Project Intake Form", "PMO Dashboard"])

if page == "Project Intake Form":
    intake_form_page()
else:
    pmo_dashboard_page()