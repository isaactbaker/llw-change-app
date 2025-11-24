# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.sql import insert, select
import logic 

# Import setup
from database import engine, capability_assessments_table, vendor_registry_table
from logic import curate_pathway, calculate_behavioural_gap, QBE_AI_PRINCIPLES, check_compliance_risk 
from ai_logic import run_compliance_brief_generator # Import new AI function


# --- App Configuration ---
st.set_page_config(
    page_title="QBE AI Workforce Evolution",
    page_icon="🚀",
    layout="wide"
)

# --- Helper: Seed Vendors if Empty ---
def seed_vendors():
    with engine.connect() as conn:
        existing = conn.execute(select(vendor_registry_table)).fetchall()
        if not existing:
            conn.execute(insert(vendor_registry_table), logic.DEFAULT_VENDORS)
            conn.commit()

# Run seed on app load
seed_vendors()

# --- 1. The Capability Needs Assessment (Intake) ---
def intake_form_page():
    st.title("🚀 QBE AI Workforce Evolution Engine")
    st.markdown("""
    **Welcome.** This tool helps us curate the right leadership and behaviour change initiatives to deliver QBE's AI Strategy.
    Use this form to assess a cohort's needs, identify behavioural gaps, and generate a recommended learning pathway.
    """)

    # Use a session state dictionary to store current form inputs for the independent button handler
    # This prevents the brief generator from crashing when trying to access form inputs outside the form block
    current_inputs = {}

    with st.form(key="assessment_form"):
        st.subheader("1. Cohort Profile")
        col1, col2 = st.columns(2)
        
        cohort_name = col1.text_input("Cohort Name (e.g., 'North America Claims Leadership') *")
        department = col2.selectbox("Function/Department", ["Claims", "Underwriting", "Technology", "HR/People", "Finance", "Operations", "Legal/Risk"])
        
        region = col1.selectbox("Region *", ["AUSPAC", "North America", "Europe", "EO (Equal Opportunities)", "Group Shared Services", "Global"])
        cohort_size = col2.selectbox("Cohort Size (Approx.)", ["1-20 (Pilot)", "20-100 (Unit)", "100+ (Division)"])
        
        audience_level = st.selectbox("Target Audience Level *", 
                                      ["Global Executive", "Senior Leader", "People Leader", "Technical Specialist", "General Workforce"],
                                      help="Determines strategic focus.")

        st.subheader("2. Diagnostic & Behavioural Gap")
        col1, col2 = st.columns(2)
        
        current_maturity = col1.selectbox("Current AI Maturity", 
                                             ["Skeptic (Resistant)", "Observer (Passive)", "Experimenter (Ad-hoc)", "Adopter (Scaling)", "Leader (Pioneering)"])
        
        primary_behavioural_gap = col2.selectbox("Primary Behavioural Shift Required *", 
                                                 [
                                                     "From Risk Aversion -> Intelligent Risk Taking",
                                                     "From Knowledge Hoarding -> Collaborative Curation",
                                                     "From 'Doing the Task' -> 'Auditing the Output'",
                                                     "From Gut-Feel -> Data-Augmented Decisions",
                                                     "From Fixed Mindset -> Continuous Learning"
                                                 ])
        
        learning_need_focus = st.selectbox("Primary Learning Focus", ["Strategic Leadership", "Technical Hard Skills", "Soft Skills & Resilience", "Operational Efficiency"])
        
        # NEW: Vendor Selection from DB
        try:
            vendor_df = pd.read_sql_table("vendor_registry", engine)
            vendor_list = vendor_df['vendor_name'].tolist()
        except:
            vendor_list = ["Gartner", "Microsoft"] # Fallback
            
        selected_vendor = st.selectbox("Preferred Vendor (Optional)", ["Auto-Assign"] + vendor_list)

        # NEW: Behavioural Shift Quantification (Tier 1 Feature)
        st.markdown("---")
        st.subheader("3. Behavioural Shift Quantification")
        c1, c2 = st.columns(2)
        baseline = c1.slider("Current Behaviour Score (1-10)", 1, 10, 4, help="1=Total Resistance, 10=Total Adoption")
        target = c2.slider("Target Behaviour Score (1-10)", 1, 10, 8, help="Where do they need to be in 12 months?")

        # Real-time gap calc (visual only here)
        gap_val = target - baseline
        if gap_val > 0:
            st.caption(f"Projected Shift: +{gap_val} points")

        # --- New Section for Governance Assurance (4. 🛡️ AI Governance Assurance Gate) ---
        st.markdown("---")
        st.subheader("4. 🛡️ AI Governance Assurance Gate")
        
        # 1.1: Governance Policy Checklist
        st.caption("Mandatory Vetting: Confirm adherence to QBE's AI Governance Policy before launch.")
        selected_principles = st.multiselect("1. AI Principle Alignment (Select all relevant):", QBE_AI_PRINCIPLES, default=QBE_AI_PRINCIPLES[:2])
        
        # Simulating a basic required checklist (1.1)
        col_v1, col_v2 = st.columns(2)
        content_vetted = col_v1.checkbox("2. Content screened for bias/misleading claims?", value=False)
        security_protocol = col_v2.checkbox("3. Data Security Protocol confirmed for region?", value=False)
        
        # Check status for saving
        governance_status = "Complete" if content_vetted and security_protocol and len(selected_principles) > 0 else "Incomplete"
        if governance_status == "Complete":
            st.success("Governance Checklist Status: Complete. Program is viable.")
        else:
            st.warning("Governance Checklist Status: Incomplete. Review required.")
        
        st.markdown("---")

        # Save current inputs to session state for the independent AI button
        current_inputs = {
            "region": region,
            "department": department,
            "learning_need_focus": learning_need_focus,
            "selected_vendor": selected_vendor
        }
        st.session_state['current_form_inputs'] = current_inputs
        st.session_state['governance_status'] = governance_status
        
        submitted = st.form_submit_button("Analyze & Generate Pathway")
        
    # --- Handler for the independent AI Brief Button (OUTSIDE THE FORM) ---
    # This button uses the saved state to run the AI without forcing a form submit.
    if st.button("Generate Ethical Risk Brief (AI Tool)"):
        inputs = st.session_state.get('current_form_inputs', {})
        if inputs:
            with st.spinner("Generating brief for Legal & Risk..."):
                brief = run_compliance_brief_generator(
                    region=inputs['region'], 
                    department=inputs['department'], 
                    program_focus=inputs['learning_need_focus'], 
                    vendor_name=inputs['selected_vendor']
                )
                st.session_state['brief_output'] = brief
                st.session_state['brief_run_status'] = 'ready'
                st.rerun() 
        else:
            st.error("Please fill out the form before generating the brief.")


    if submitted:
        # Use the stored governance status from the form submission state
        final_governance_status = st.session_state.get('governance_status', 'Incomplete')
        
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
                "current_maturity": current_maturity.split(" ")[0],
                "primary_behavioural_gap": primary_behavioural_gap,
                "learning_need_focus": learning_need_focus
            }

            # 2. Run Logic
            result = curate_pathway(form_data)
            
            # Calculate final vendor and compliance risk check (1.2)
            final_vendor = result['recommended_vendor'] if selected_vendor == "Auto-Assign" else selected_vendor
            compliance_risk = check_compliance_risk(region, final_vendor) # NEW RISK CHECK

            if compliance_risk: # Display the flag (1.2)
                st.error(f"GOVERNANCE RISK WARNING: {compliance_risk}")
            
            # Calculate Gap Tag
            _, gap_tag = calculate_behavioural_gap(baseline, target)

            # Merge for saving
            db_record = {
                **form_data,
                "urgency_score": result['urgency_score'],
                "recommended_pathway": result['recommended_pathway'],
                "governance_checklist_status": final_governance_status, # NEW FIELD
                "recommended_vendor": result['recommended_vendor'],  
                "estimated_budget": result['estimated_budget'],
                "baseline_behavior_score": baseline,
                "target_behavior_score": target,
                "selected_vendor": final_vendor
            }

            # 3. Save
            with engine.connect() as conn:
                conn.execute(insert(capability_assessments_table).values(db_record))
                conn.commit()

            # 4. Display Output
            st.success("Assessment Complete. Strategic Pathway Generated.")
            
            st.subheader(f"🎯 Curated Pathway: {result['recommended_pathway']}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Urgency Score", f"{result['urgency_score']}/100")
            col2.metric("Vendor Strategy", final_vendor)
            col3.metric("Est. Budget", f"${result['estimated_budget']:,}")
            
            st.info(f"**Gap Analysis:** {target-baseline} point delta. **{gap_tag}**")
            st.progress(baseline/10)

    # --- Display Generated Brief (Below the main form logic) ---
    if st.session_state.get('brief_run_status') == 'ready':
         st.subheader("📄 Ethical Risk Brief Output")
         st.markdown(st.session_state['brief_output'])
         
         # Reset run status after displaying
         st.session_state['brief_run_status'] = 'displayed'
         st.session_state['brief_output'] = st.session_state['brief_output'] # Keep output for rerun stability


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
        st.error(f"Database Error: {e}")
        return

    # --- Row 1: Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cohorts Assessed", len(df))
    col2.metric("Total Projected Investment", f"${df['estimated_budget'].sum():,.0f}")
    
    avg_gap = (df['target_behavior_score'] - df['baseline_behavior_score']).mean()
    col3.metric("Avg. Behavioural Gap", f"{avg_gap:.1f} pts")

    st.markdown("---")

    # --- Row 2: Global Heatmap (Tier 1 Feature) ---
    st.subheader("🌍 Global AI Maturity Heatmap")
    
    # Prepare map data
    map_data = []
    maturity_map = {"Skeptic": 1, "Observer": 2, "Experimenter": 3, "Adopter": 4, "Leader": 5}
    
    for index, row in df.iterrows():
        region = row['region']
        # Extract first word of maturity string safely
        mat_str = row['current_maturity'].split(" ")[0] if row['current_maturity'] else "Observer"
        score = maturity_map.get(mat_str, 2)
        
        if region in logic.REGION_ISO_MAP:
            for iso in logic.REGION_ISO_MAP[region]:
                map_data.append({"iso_alpha": iso, "maturity": score, "cohort": row['cohort_name']})
    
    if map_data:
        df_map = pd.DataFrame(map_data)
        df_map_agg = df_map.groupby("iso_alpha")['maturity'].mean().reset_index()
        
        fig_map = px.choropleth(
            df_map_agg,
            locations="iso_alpha",
            color="maturity",
            hover_name="iso_alpha",
            color_continuous_scale="RdYlGn",
            range_color=[1, 5],
            title="Maturity Intensity by Operating Region"
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Not enough regional data to generate map.")

    # --- Row 3: Behavioural Shift Tracker (Tier 1 Feature) ---
    col1, col2 = st.columns(2)
    
    # Chart 1: Vendor Performance (Scatter)
    try:
        vendor_df = pd.read_sql_table("vendor_registry", engine)
        # Merge assessment spend into vendor data
        spend_by_vendor = df.groupby('selected_vendor')['estimated_budget'].sum().reset_index()
        vendor_perf = pd.merge(vendor_df, spend_by_vendor, left_on='vendor_name', right_on='selected_vendor', how='left').fillna(0)
        
        fig_perf = px.scatter(vendor_perf, x='estimated_budget', y='performance_rating', 
                              size='avg_daily_rate', color='vendor_name',
                              title="Vendor Strategic Value (Spend vs. Rating)",
                              labels={'estimated_budget': 'Total QBE Spend', 'performance_rating': 'Quality Rating (1-5)'})
        col1.plotly_chart(fig_perf, use_container_width=True)
    except:
        col1.info("Vendor data pending.")

    # Chart 2: Behavioural Shift (Slope/Dumbbell Chart Logic)
    # Using a bar chart showing Start vs Target for top cohorts
    df_shift = df.head(10).copy() # Top 10 for readability
    fig_shift = go.Figure()
    fig_shift.add_trace(go.Bar(x=df_shift['cohort_name'], y=df_shift['baseline_behavior_score'], name='Current State', marker_color='orange'))
    fig_shift.add_trace(go.Bar(x=df_shift['cohort_name'], y=df_shift['target_behavior_score']-df_shift['baseline_behavior_score'], name='Target Growth', marker_color='green'))
    fig_shift.update_layout(barmode='stack', title="Behavioural Shift Goals (Top Cohorts)")
    col2.plotly_chart(fig_shift, use_container_width=True)

    # --- Row 4: Data ---
    st.subheader("Cohort Registry")
    st.dataframe(df[['cohort_name', 'region', 'audience_level', 'recommended_pathway', 'baseline_behavior_score', 'target_behavior_score', 'governance_checklist_status']], use_container_width=True)

# --- Main App Router ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Capability Assessment", "Strategy Dashboard"])

if page == "Capability Assessment":
    # Initialize session state for brief output control
    if 'brief_output' not in st.session_state:
        st.session_state['brief_output'] = None
    if 'brief_run_status' not in st.session_state:
        st.session_state['brief_run_status'] = 'initial'
    if 'current_form_inputs' not in st.session_state:
        st.session_state['current_form_inputs'] = {}
        
    intake_form_page()
else:
    # Clear brief state when switching tabs
    st.session_state['brief_output'] = None
    st.session_state['brief_run_status'] = 'initial'
    strategy_dashboard_page()
