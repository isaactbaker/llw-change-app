# database.py
import sqlalchemy

# Define the database connection
# NEW FILENAME to force schema update
DATABASE_URL = "sqlite:///./qbe_evolution_v2.db"
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
    
    # NEW: Vendor Linkage
    sqlalchemy.Column("selected_vendor", sqlalchemy.String),
    
    # Output Fields
    sqlalchemy.Column("urgency_score", sqlalchemy.Integer),
    sqlalchemy.Column("recommended_pathway", sqlalchemy.String),
    sqlalchemy.Column("estimated_budget", sqlalchemy.Integer),
    
    # Management Fields
    sqlalchemy.Column("status", sqlalchemy.String, default="Proposed"),
    sqlalchemy.Column("submission_date", sqlalchemy.DateTime, default=sqlalchemy.func.now())
)

# 2. Vendor Registry (NEW - Tier 1 Feature)
vendor_registry_table = sqlalchemy.Table(
    "vendor_registry",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("vendor_name", sqlalchemy.String),
    sqlalchemy.Column("specialty", sqlalchemy.String),
    sqlalchemy.Column("avg_daily_rate", sqlalchemy.Integer),
    sqlalchemy.Column("performance_rating", sqlalchemy.Integer), # 1-5 Stars
    sqlalchemy.Column("status", sqlalchemy.String, default="Active")
)

# 3. Behavioural Pulse Checks (NEW - Tier 1 Feature)
behaviour_pulse_table = sqlalchemy.Table(
    "behaviour_pulse_checks",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("assessment_id", sqlalchemy.Integer), # FK to Cohort
    sqlalchemy.Column("check_date", sqlalchemy.String),
    sqlalchemy.Column("new_score", sqlalchemy.Integer),
    sqlalchemy.Column("notes", sqlalchemy.String)
)

# Create the tables
metadata.create_all(engine)