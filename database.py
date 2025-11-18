# database.py
import sqlalchemy

# Define the database connection
# We use a NEW file name to force a fresh schema creation
DATABASE_URL = "sqlite:///./qbe_evolution_v1.db"
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# 1. Main Capability Assessment Table (The "Cohort")
capability_assessments_table = sqlalchemy.Table(
    "capability_assessments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("cohort_name", sqlalchemy.String), # e.g. "North America Claims Team"
    sqlalchemy.Column("department", sqlalchemy.String),
    sqlalchemy.Column("region", sqlalchemy.String), # Global, AUSPAC, NA, etc.
    sqlalchemy.Column("audience_level", sqlalchemy.String), # Exec, Leader, Tech, General
    sqlalchemy.Column("cohort_size", sqlalchemy.String),
    
    # Diagnosis Fields
    sqlalchemy.Column("current_maturity", sqlalchemy.String), # Skeptic, Observer, Experimenter, etc.
    sqlalchemy.Column("primary_behavioural_gap", sqlalchemy.String), # Risk Aversion, etc.
    sqlalchemy.Column("learning_need_focus", sqlalchemy.String), # Technical, Strategic, Soft Skills
    
    # Output Fields
    sqlalchemy.Column("urgency_score", sqlalchemy.Integer), # Calculated
    sqlalchemy.Column("recommended_pathway", sqlalchemy.String), # The Program Name
    sqlalchemy.Column("recommended_vendor", sqlalchemy.String), # The Vendor
    sqlalchemy.Column("estimated_budget", sqlalchemy.Integer),
    
    # Management Fields
    sqlalchemy.Column("status", sqlalchemy.String, default="Proposed"), # Proposed, Active, Completed
    sqlalchemy.Column("submission_date", sqlalchemy.DateTime, default=sqlalchemy.func.now())
)

# 2. Program Impact/Health Table (ROI Tracking)
program_impact_table = sqlalchemy.Table(
    "program_impact",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("assessment_id", sqlalchemy.Integer), # Links to the Cohort
    sqlalchemy.Column("log_date", sqlalchemy.String),
    
    # Impact Metrics
    sqlalchemy.Column("participant_satisfaction", sqlalchemy.Integer), # 1-5
    sqlalchemy.Column("confidence_improvement", sqlalchemy.Integer), # % increase
    sqlalchemy.Column("behaviour_shift_observed", sqlalchemy.String), # "Yes/No/Partial"
    sqlalchemy.Column("notes", sqlalchemy.String)
)

# Create the tables
metadata.create_all(engine)