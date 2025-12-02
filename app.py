# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.sql import insert, select
import logic
import database 

# Import setup
from database import engine, capability_assessments_table, vendor_registry_table, individual_diagnostics_table
from logic import curate_pathway, calculate_behavioural_gap, check_compliance_risk, SWP_WORKSTREAMS, EXECUTION_STATUSES, calculate_execution_score

from ai_logic import run_compliance_brief_generator, run_ldp_protocol_generator, run_status_anchor_dialogue

# --- App Configuration ---
st.set_page_config(
    page_title="QBE AI Workforce Evolution",
    page_icon="🚀",
    layout="wide"
)

# --- GLOBAL CONFIGURATION DATA (EMBEDDED PRINCIPLES) ---
QBE_AI_PRINCIPLES = [
    "Fairness (Prevent Bias/Discrimination)",
    "Privacy (Data Safeguarding)",
    "Transparency (Disclosure of AI Use)",
    "Explainability (Intelligibility of Outcomes)",
    "Accountability (Human Oversight)",
    "Benefit & Safety (Prevent Harm)"
]


# --- Helper: Seed Vendors if Empty ---
def seed_vendors():
    with engine.connect() as conn:
        existing = conn.execute(select(vendor_registry_table)).fetchall()
        if not existing:
            conn.execute(insert(vendor_registry_table), logic.DEFAULT_VENDORS)
            conn.commit()

# Run seed on app load
seed_vendors()


# --- NEW PAGE: Individual Coach Architect (LDP Engine) ---
def ldp_engine_page():
    st.title("👤 Individual Coach Architect (LDP Engine)")
    st.markdown("""
    **Architecture:** This tool translates psychological diagnostics into personalized 90-Day Development Protocols and Coaching Goals, ensuring development is scientifically rigorous and scalable.
    """)
    
    with st.form(key="ldp_form"):
        st.subheader("1. Diagnostic Input (COM-B & Leadership)")
        
        col1, col2 = st.columns(2)
        leader_name = col1.text_input("Leader Name/ID *")
        leader_role = col2.selectbox("Role Level *", ["Global Executive", "Senior Leader", "People Leader"])

        st.markdown("---")
        st.subheader("2. Behavioral Assessment Scores (1-10)")
        
        c1, c2, c3 = st.columns(3)
        loc_score = c1.slider("LOC/Anxiety Score (Loss of Control)", 1, 10, 6, help="High score = High Anxiety over Black Box decisions.")
        ambidextrous_score = c2.slider("Ambidextrous Score (Innovation vs. Stability)", 1, 10, 5, help="Score leader's ability to balance exploitation/exploration.")
        com_b_score = c3.slider("Overall COM-B Resistance Score", 1, 10, 5, help="Calculated resistance level.")

# --- Conceptual Inputs for AI Generation (Used by both buttons) ---
        primary_barrier = st.selectbox("Identified Primary Barrier (From COM-B Audit)", ["Status Threat", "Loss of Control (LOC)", "Social Norm Barrier", "Skill Deficit"])
        theme = st.selectbox("Core Development Theme", ["Ambidextrous Supervision", "Ethical Stewardship", "Outcome Orchestration"])

        
        st.markdown("---")
        st.subheader("3. 🧠 Strategic Behavioral & Ethical Diagnostic")
        st.caption("Rate your agreement (1=Strongly Disagree, 5=Strongly Agree) unless specified.")

        col_eth, col_safety = st.columns(2)

        # Ethical Stewardship & Accountability
        col_eth.markdown("**Ethical Stewardship & Accountability**")
        ethical_a_score = col_eth.slider("Q1: Primary risk from an AI error lies with the person who approves the output, not the machine.", 1, 5, 4)
        ethical_b_input = col_eth.text_area("Q2: Given a claims denial based on AI, how would you coach your team member to communicate the final decision?", height=100) # Open Text

        # Psychological Safety & Resilience
        col_safety.markdown("**Psychological Safety & Resilience**")
        safety_a_score = col_safety.slider("Q3: My team feels comfortable reporting an AI 'hallucination' or error without fear of being penalized.", 1, 5, 3)
        safety_b_score = col_safety.slider("Q4: When a new AI tool automates 30% of my team's old tasks, I focus on training them for new roles.", 1, 5, 4)

        col_collab, col_growth = st.columns(2)

        # Intentional Collaboration (Silo Reduction)
        col_collab.markdown("**Intentional Collaboration (Silo Reduction)**")
        collab_a_score = col_collab.slider("Q5: My department's success is fundamentally tied to the success of the Technology and Claims departments.", 1, 5, 5)
        collab_b_score = col_collab.slider("Q6: I actively seek input from the Compliance/Legal team during the initial design phase of a new business process.", 1, 5, 4)

        # Growth Mindset & Continuous Learning
        col_growth.markdown("**Growth Mindset & Continuous Learning**")
        growth_a_score = col_growth.slider("Q7: I believe my ability to learn new AI-related skills is unlimited, regardless of my current technical background.", 1, 5, 4)
        growth_b_score = col_growth.slider("Q8: I allocate protected time (e.g., 2 hours per week) for myself and my team to experiment with new digital tools.", 1, 5, 3)
        
        submitted = st.form_submit_button("Generate 90-Day Protocol")


    # --- ACTION BUTTONS (OUTSIDE THE FORM) ---
    st.markdown("---")


    # NEW: Status Anchor Dialogue button handler (Moved outside the form to fix StreamlitAPIException)
    if st.button("Generate Status Anchor Dialogue (AI Coach)"):
        # We need the last submitted/defined values for the AI call context
        inputs = st.session_state.get('current_form_inputs', {})
        
        # Retrieve scores that might not be in 'current_form_inputs' but are needed for the AI call
        # Since these variables were defined *inside* the form, we rely on the state from the last full form submission (if submitted) 
        # or mock values if running standalone. For the demo, we use the last form state values for safety.

        if inputs:
            with st.spinner("Generating personalized coaching dialogue..."):
                # Call the NEW Status Anchor Dialogue function
                dialogue_text = run_status_anchor_dialogue(
                    leader_role=inputs['audience_level'], # Using cohort level as proxy for leader_role
                    primary_barrier=inputs['primary_behavioural_gap'], # Using cohort gap as proxy for barrier
                    loc_score=st.session_state.get('loc_score', 6), # Safely use hardcoded defaults if necessary
                    growth_a=st.session_state.get('growth_a_score', 4) # Safely use hardcoded defaults if necessary
                )
                
                st.session_state['dialogue_output'] = dialogue_text
                st.session_state['dialogue_run_status'] = 'ready'
                st.rerun() 
        else:
            st.warning("Please submit the main form once to load diagnostic context.")
            

    
    if submitted and leader_name:
        with st.spinner("Generating individualized coaching protocol..."):
            # Call the updated AI function with all 13 inputs
            protocol = run_ldp_protocol_generator(
                leader_role=leader_role,
                primary_barrier=primary_barrier,
                theme=theme,
                loc_score=loc_score,
                ambidextrous_score=ambidextrous_score,
                ethical_a=ethical_a_score,
                ethical_b=ethical_b_input, 
                safety_a=safety_a_score,
                safety_b=safety_b_score,
                collab_a=collab_a_score,
                collab_b=collab_b_score,
                growth_a=growth_a_score,
                growth_b=growth_b_score
            )
            
            # Save the diagnostic result to the DB
            db_record = {
                "leader_name": leader_name,
                "role_level": leader_role,
                "loc_score": loc_score,
                "ambidextrous_score": ambidextrous_score,
                "com_b_score": com_b_score,
                "primary_barrier": primary_barrier,
                "core_development_theme": theme,
                "protocol_generated": protocol,
                
                # Saving the 8 New Diagnostic Fields:
                "ethical_a_score": ethical_a_score,
                "ethical_b_score": ethical_b_input, 
                "safety_a_score": safety_a_score,
                "safety_b_score": safety_b_score,
                "collab_a_score": collab_a_score,
                "collab_b_score": collab_b_score,
                "growth_a_score": growth_a_score,
                "growth_b_score": growth_b_score
            }
            with engine.connect() as conn:
                conn.execute(insert(individual_diagnostics_table).values(db_record))
                conn.commit()

        st.success(f"Protocol Generated for {leader_name}. Ready for deployment via AI Coach App.")
        st.markdown("---")
        st.subheader("3. 90-Day Development Protocol (AI Coach Output)")
        st.markdown(protocol)
        
        # Display static Coaching Dialogue prompt concept (Optional visual aid)
        st.caption("Conceptual Model: This protocol forms the core of the personalized AI Coach dialogue prompts (e.g., Conversation Design).")


    # --- Display Logic for the new button (Placed after the main form) ---
    if st.session_state.get('dialogue_run_status') == 'ready':
        st.markdown("---")
        st.subheader("🗣️ Status Anchor Dialogue (Just-in-Time Coaching)")
        st.info(st.session_state['dialogue_output'])
        # Reset status after displaying
        st.session_state['dialogue_run_status'] = 'displayed'
        st.session_state['dialogue_output'] = st.session_state['dialogue_output'] # Keep output for rerun stability
    
    # --- Display Generated Brief (Below the main form logic) ---
    if st.session_state.get('brief_run_status') == 'ready':
         st.subheader("📄 Ethical Risk Brief Output")
         st.markdown(st.session_state['brief_output'])
         
         # Reset run status after displaying
         st.session_state['brief_run_status'] = 'displayed'
         st.session_state['brief_output'] = st.session_state['brief_output'] # Keep output for rerun stability


# --- 1. The Capability Needs Assessment (Intake) ---
def intake_form_page():
    st.title("🚀 QBE AI Workforce Evolution Engine")
    st.markdown("""
    **Welcome.** This tool helps us curate the right leadership and behaviour change initiatives to deliver QBE's AI Strategy.
    Use this form to assess a cohort's needs, identify behavioural gaps, and generate a recommended learning pathway.
    """)

    # Use a session state dictionary to store current form inputs for the independent button handler
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

        # --- NEW EXECUTION/COORDINATION INPUTS (Module 3) ---
        st.markdown("---")
        st.subheader("3. Execution & Coordination")
        
        col_exec, col_swp = st.columns(2)
        
        # NEW: Execution Status
        execution_status = col_exec.selectbox("Program Status", logic.EXECUTION_STATUSES, index=0)
        
        # NEW: SWP Workstream Linkage
        swp_workstream = col_swp.selectbox("SWP Workstream Linkage", logic.SWP_WORKSTREAMS, help="Links program to AI Workforce Strategy priorities.")
        
        
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
                "selected_vendor": final_vendor,
                "execution_status": execution_status, # NEW FIELD
                "swp_workstream": swp_workstream # NEW FIELD
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


# --- 2. The Global Strategy Dashboard (Enterprise Talent Command Centre) ---
def strategy_dashboard_page():
    st.title("🌍 Global AI Workforce Strategy Dashboard (Command Centre)")
    st.markdown("Tracking maturity, investment, and behavioural shifts across the enterprise.")

    try:
        df = pd.read_sql_table("capability_assessments", engine)
        if df.empty:
            st.info("No data yet. Please submit assessments via the 'Capability Assessment' tab.")
            return
    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    # Recalculate metrics
    readiness_data = calculate_execution_score(df)
    
    # --- Row 1: Metrics ---
    col1, col2, col3, col4 = st.columns(4) 
    col1.metric("Total Cohorts Assessed", len(df))
    col2.metric("Total Projected Investment", f"${df['estimated_budget'].sum():,.0f}")
    
    # NEW METRIC: Execution Score (Module 3)
    col3.metric("Strategic Execution Score", f"{readiness_data['readiness_score']}%", 
                help="Weighted score favoring Scaling and Complete programs.")
    col4.metric("Programs Completed", f"{readiness_data['complete_count']}")
    
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

    st.markdown("---")

    # --- NEW EXECUTION TRACKING CHARTS (Module 3) ---
    col1, col2 = st.columns(2)
    
    # Chart 3: Program Execution Status (New Donut Chart)
    fig_exec = px.pie(df, names='execution_status', title='Global Program Execution Status')
    col1.plotly_chart(fig_exec, use_container_width=True)
    
    # Chart 4: SWP Workstream Coordination (New Bar Chart)
    fig_swp = px.histogram(df, x='swp_workstream', title='Coordination: Programs by SWP Workstream')
    col2.plotly_chart(fig_swp, use_container_width=True)
    
    # --- Row 4: Data ---
    st.subheader("Cohort Registry")
    display_cols = ['cohort_name', 'region', 'audience_level', 'recommended_pathway', 
                    'execution_status', 'swp_workstream', 'governance_checklist_status']
    st.dataframe(df[display_cols], use_container_width=True)

# --- Main App Router ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Capability Assessment", "Strategy Dashboard", "Individual Coach Architect"])

if page == "Capability Assessment":
    # Initialize session state for brief output control
    if 'brief_output' not in st.session_state:
        st.session_state['brief_output'] = None
    if 'brief_run_status' not in st.session_state:
        st.session_state['brief_run_status'] = 'initial'
    if 'current_form_inputs' not in st.session_state:
        st.session_state['current_form_inputs'] = {}
        
    intake_form_page()
elif page == "Strategy Dashboard":
    # Clear brief state when switching tabs
    st.session_state['brief_output'] = None
    st.session_state['brief_run_status'] = 'initial'
    strategy_dashboard_page()
elif page == "Individual Coach Architect":
    # Initialize session state variables for the new dialogue output
    if 'dialogue_output' not in st.session_state:
        st.session_state['dialogue_output'] = None
    if 'dialogue_run_status' not in st.session_state:
        st.session_state['dialogue_run_status'] = 'initial'
        
    # Clear brief state when switching tabs (Optional, but safe)
    st.session_state['brief_output'] = None
    st.session_state['brief_run_status'] = 'initial'
    ldp_engine_page()
