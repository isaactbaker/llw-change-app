# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import insert, select

# Import our setup
from database import engine, capability_assessments_table, program_impact_table
from logic import curate_pathway

# --- App Configuration ---
st.set_page_config(
    page_title="QBE AI Workforce Evolution",
    page_icon="🚀",
    layout="wide"
)

# --- 1. The Capability Needs Assessment (Intake) ---
def intake_form_page():
    st.title("🚀 QBE AI Workforce Evolution Engine")
    st.markdown("""
    **Welcome.** This tool helps us curate the right leadership and behaviour change initiatives to deliver QBE's AI Strategy.
    Use this form to assess a cohort's needs, identify behavioural gaps, and generate a recommended learning pathway.
    """)

    with st.form(key="assessment_form"):
        st.subheader("1. Cohort Profile")
        col1, col2 = st.columns(2)
        
        cohort_name = col1.text_input("Cohort Name (e.g., 'North America Claims Leadership') *")
        department = col2.selectbox("Function/Department", ["Claims", "Underwriting", "Technology", "HR/People", "Finance", "Operations", "Legal/Risk"])
        
        region = col1.selectbox("Region *", ["AUSPAC", "North America", "Europe", "EO (Equal Opportunities)", "Group Shared Services", "Global"])
        cohort_size = col2.selectbox("Cohort Size (Approx.)", ["1-20 (Pilot)", "20-100 (Unit)", "100+ (Division)"])
        
        audience_level = st.selectbox("Target Audience Level *", 
                                      ["Global Executive", "Senior Leader", "People Leader", "Technical Specialist", "General Workforce"],
                                      help="This determines the complexity and strategic focus of the curated program.")

        st.subheader("2. Diagnostic & Behavioural Gap")
        col1, col2 = st.columns(2)
        
        current_maturity = col1.selectbox("Current AI Maturity", 
                                          ["Skeptic (Resistant)", "Observer (Passive)", "Experimenter (Ad-hoc)", "Adopter (Scaling)", "Leader (Pioneering)"],
                                          help="Skeptic: Views AI as threat. Experimenter: Uses tools occasionally.")
        
        primary_behavioural_gap = col2.selectbox("Primary Behavioural Shift Required *", 
                                                 [
                                                     "From Risk Aversion -> Intelligent Risk Taking",
                                                     "From Knowledge Hoarding -> Collaborative Curation",
                                                     "From 'Doing the Task' -> 'Auditing the Output'",
                                                     "From Gut-Feel -> Data-Augmented Decisions",
                                                     "From Fixed Mindset -> Continuous Learning"
                                                 ])
        
        learning_need_focus = st.selectbox("Primary Learning Focus", ["Strategic Leadership", "Technical Hard Skills", "Soft Skills & Resilience", "Operational Efficiency"])

        st.markdown("---")
        submitted = st.form_submit_button("Analyze & Generate Pathway")

    if submitted:
        if not cohort_name:
            st.error("Please enter a Cohort Name.")
        else:
            # 1. Prepare Data
            form_data = {
                "cohort_name": cohort_name,
                "department": department,
                "region": region,
                "audience_level": audience_level,
                "cohort_size": cohort_size,
                "current_maturity": current_maturity.split(" ")[0], # Just take the first word
                "primary_behavioural_gap": primary_behavioural_gap,
                "learning_need_focus": learning_need_focus
            }

            # 2. Run Logic (The Intelligence Layer)
            # This calls the 'Curator' function in logic.py
            result = curate_pathway(form_data)
            
            # Merge result into form_data for saving
            full_record = {**form_data, **result}
            # Remove the 'program_description' from DB save (it's just for display)
            db_record = {k:v for k,v in full_record.items() if k != "program_description"}

            # 3. Save to Database
            with engine.connect() as conn:
                conn.execute(insert(capability_assessments_table).values(db_record))
                conn.commit()

            # 4. Display "The Recommendation"
            st.success("Assessment Complete. Strategic Pathway Generated.")
            
            st.subheader(f"🎯 Curated Pathway: {result['recommended_pathway']}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Urgency Score", f"{result['urgency_score']}/100", help="Higher score = Higher strategic risk/priority.")
            col2.metric("Recommended Vendor", result['recommended_vendor'])
            col3.metric("Est. Budget", f"${result['estimated_budget']:,}")

            st.info(f"**Behavioural Focus:** Addressing the gap: *{primary_behavioural_gap}*")
            st.markdown(result['program_description'])


# --- 2. The Global Strategy Dashboard ---
def strategy_dashboard_page():
    st.title("🌍 Global AI Workforce Strategy Dashboard")
    st.markdown("Tracking maturity, investment, and behavioural shifts across the enterprise.")

    try:
        df = pd.read_sql_table("capability_assessments", engine)
        if df.empty:
            st.info("No data yet. Please submit assessments via the 'Capability Assessment' tab.")
            return
    except Exception as e:
        st.error("Database Error. Please ensure database.py is updated.")
        return

    # --- Row 1: High Level Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cohorts Assessed", len(df))
    total_spend = df['estimated_budget'].sum()
    col2.metric("Total Projected Investment", f"${total_spend:,.0f}")
    
    # Calculate % of "Skeptics"
    skeptic_count = len(df[df['current_maturity'] == 'Skeptic'])
    skeptic_pct = (skeptic_count / len(df)) * 100
    col3.metric("Risk Metric: % Skeptics", f"{skeptic_pct:.1f}%")

    st.markdown("---")

    # --- Row 2: The "Heatmap" & Vendors ---
    col1, col2 = st.columns(2)
    
    # Chart 1: Regional Maturity Heatmap
    # We map maturity text to numbers for averaging
    maturity_map = {"Skeptic": 1, "Observer": 2, "Experimenter": 3, "Adopter": 4, "Leader": 5}
    df['maturity_score'] = df['current_maturity'].map(maturity_map)
    
    avg_maturity_by_region = df.groupby('region')['maturity_score'].mean().reset_index()
    
    fig_map = px.bar(avg_maturity_by_region, x='region', y='maturity_score',
                     title="Global AI Maturity by Region (1-5)",
                     color='maturity_score', 
                     color_continuous_scale='RdYlGn', # Red to Green
                     range_y=[0,5])
    col1.plotly_chart(fig_map, use_container_width=True)

    # Chart 2: Vendor Utilization
    fig_vendor = px.pie(df, names='recommended_vendor', title="Vendor Strategy Distribution", hole=0.4)
    col2.plotly_chart(fig_vendor, use_container_width=True)

    # --- Row 3: Behavioural Gaps ---
    st.subheader("🧠 Behavioural Gap Analysis")
    st.markdown("What is holding our workforce back?")
    
    gap_counts = df['primary_behavioural_gap'].value_counts().reset_index()
    gap_counts.columns = ['Gap', 'Count']
    
    fig_gaps = px.bar(gap_counts, x='Count', y='Gap', orientation='h',
                      title="Top Behavioural Barriers Identified",
                      color='Count')
    st.plotly_chart(fig_gaps, use_container_width=True)

    # --- Row 4: Data Table ---
    st.subheader("Cohort Registry")
    st.dataframe(df[['cohort_name', 'region', 'audience_level', 'recommended_pathway', 'status']], use_container_width=True)

# --- Main App Router ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Capability Assessment", "Strategy Dashboard"])

if page == "Capability Assessment":
    intake_form_page()
else:
    strategy_dashboard_page()