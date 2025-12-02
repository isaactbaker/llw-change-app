# database.py
import sqlalchemy

# Define the database connection
# CHANGED VERSION TO v3 TO FORCE REBUILD
DATABASE_URL = "sqlite:///./qbe_evolution_v5.db"
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# 1. Main Capability Assessment Table (The "Cohort")
capability_assessments_table = sqlalchemy.Table(
    "capability_assessments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("cohort_name", sqlalchemy.String), 
    sqlalchemy.Column("department", sqlalchemy.String),
    sqlalchemy.Column("region", sqlalchemy.String), 
    sqlalchemy.Column("audience_level", sqlalchemy.String), 
    sqlalchemy.Column("cohort_size", sqlalchemy.String),
    
    # Diagnosis Fields
    sqlalchemy.Column("current_maturity", sqlalchemy.String), 
    sqlalchemy.Column("primary_behavioural_gap", sqlalchemy.String), 
    sqlalchemy.Column("learning_need_focus", sqlalchemy.String), 
    
    # NEW: Behavioural Delta Fields
    sqlalchemy.Column("baseline_behavior_score", sqlalchemy.Integer),
    sqlalchemy.Column("target_behavior_score", sqlalchemy.Integer),

    # NEW FIELD FOR GOVERNANCE ASSURANCE (1.1)
    sqlalchemy.Column("governance_checklist_status", sqlalchemy.String, default="Incomplete"), # Stores the final status
    
    # NEW: Vendor Linkage
    sqlalchemy.Column("selected_vendor", sqlalchemy.String),      # <--- CHECK 1
    
    # Output Fields
    sqlalchemy.Column("urgency_score", sqlalchemy.Integer), 
    sqlalchemy.Column("recommended_pathway", sqlalchemy.String), 
    sqlalchemy.Column("recommended_vendor", sqlalchemy.String),   # <--- CHECK 2
    sqlalchemy.Column("estimated_budget", sqlalchemy.Integer),
    
    # NEW FIELDS FOR EXECUTION & COORDINATION
    sqlalchemy.Column("swp_workstream", sqlalchemy.String),  # Links to strategic priority
    sqlalchemy.Column("execution_status", sqlalchemy.String, default="Planning"), # Tracks delivery status
    
    # Management Fields
    sqlalchemy.Column("status", sqlalchemy.String, default="Proposed"), 
    sqlalchemy.Column("submission_date", sqlalchemy.DateTime, default=sqlalchemy.func.now())
)

# 2. Vendor Registry (ADD Compliance/Residency Fields)
vendor_registry_table = sqlalchemy.Table(
    "vendor_registry",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("vendor_name", sqlalchemy.String),
    sqlalchemy.Column("specialty", sqlalchemy.String),
    sqlalchemy.Column("avg_daily_rate", sqlalchemy.Integer),
    sqlalchemy.Column("performance_rating", sqlalchemy.Integer), 
    
    # NEW FIELDS FOR GOVERNANCE ASSURANCE (1.2)
    sqlalchemy.Column("compliance_rating", sqlalchemy.String), # e.g., Green, Yellow, Red
    sqlalchemy.Column("data_residency_cert", sqlalchemy.String), # e.g., EU-GDPR, AUS-Privacy, None
    
    sqlalchemy.Column("status", sqlalchemy.String, default="Active")
)

# 3. Behavioural Pulse Checks
behaviour_pulse_table = sqlalchemy.Table(
    "behaviour_pulse_checks",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("assessment_id", sqlalchemy.Integer), 
    sqlalchemy.Column("check_date", sqlalchemy.String),
    sqlalchemy.Column("new_score", sqlalchemy.Integer),
    sqlalchemy.Column("notes", sqlalchemy.String)
)

# 4. Individual Diagnostics Table (NEW TABLE for LDP Engine)
individual_diagnostics_table = sqlalchemy.Table(
    "individual_diagnostics",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("leader_name", sqlalchemy.String),
    sqlalchemy.Column("role_level", sqlalchemy.String),
    
    # Diagnostic Variables (MUST MATCH db_record KEYS)
    sqlalchemy.Column("loc_score", sqlalchemy.Integer),
    sqlalchemy.Column("ambidextrous_score", sqlalchemy.Integer),
    sqlalchemy.Column("com_b_score", sqlalchemy.Integer), # <--- CHECK THIS FIELD
    
    # AI Output
    sqlalchemy.Column("primary_barrier", sqlalchemy.String),  # e.g., Status Threat
    sqlalchemy.Column("core_development_theme", sqlalchemy.String), # e.g., Ambidextrous Supervision
    sqlalchemy.Column("protocol_generated", sqlalchemy.Text), # The 90-Day plan text
    sqlalchemy.Column("creation_date", sqlalchemy.DateTime, default=sqlalchemy.func.now())
)

# --- CRITICAL FIX: AGGRESSIVELY RESET VENDOR TABLE FOR SCHEMA UPDATE ---
# This ensures the vendor table is dropped if it exists, forcing a clean creation with the new columns.
# vendor_registry_table.drop(engine, checkfirst=True)


# Create the tables
metadata.create_all(engine)
