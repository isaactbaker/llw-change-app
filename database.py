# database.py
import sqlalchemy

# Define the database connection
DATABASE_URL = "sqlite:///./change_portfolio_v10.db"
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Define the table structure (just like your Lovable Table)
change_portfolio_table = sqlalchemy.Table(
    "change_portfolio",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("project_name", sqlalchemy.String),
    sqlalchemy.Column("exec_sponsor", sqlalchemy.String),
    sqlalchemy.Column("go_live_date", sqlalchemy.String),
    sqlalchemy.Column("strategic_alignment", sqlalchemy.String), 
    sqlalchemy.Column("impacted_departments", sqlalchemy.String), 
    sqlalchemy.Column("change_type", sqlalchemy.String),
    sqlalchemy.Column("scale", sqlalchemy.String),
    sqlalchemy.Column("impact_depth", sqlalchemy.String),
    sqlalchemy.Column("change_history", sqlalchemy.String),
    sqlalchemy.Column("behavioural_barrier", sqlalchemy.String), 
    sqlalchemy.Column("impact_score", sqlalchemy.Integer),
    sqlalchemy.Column("change_tier", sqlalchemy.String),
    sqlalchemy.Column("effort_score", sqlalchemy.Integer),
    sqlalchemy.Column("status", sqlalchemy.String, default="Intake"),
    sqlalchemy.Column("playbook_data", sqlalchemy.String),
    # --- END NEW COLUMN ---
    # --- NEW COLUMN FOR READINESS PLAN ---
    sqlalchemy.Column("readiness_plan_html", sqlalchemy.String),
    # --- END NEW COLUMN ---
    # --- NEW COLUMN FOR COMMS CAMPAIGN ---
    sqlalchemy.Column("comms_campaign_html", sqlalchemy.String),
    # --- END NEW COLUMN ---

    sqlalchemy.Column("submission_date", sqlalchemy.DateTime, default=sqlalchemy.func.now())
)

# --- NEW TABLE FOR AI ANALYST (IDEA #1) ---
friction_log_table = sqlalchemy.Table(
    "friction_log",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    # This links the friction to a project
    sqlalchemy.Column("project_name", sqlalchemy.String), 
    sqlalchemy.Column("friction_note", sqlalchemy.String),
    sqlalchemy.Column("status", sqlalchemy.String, default="Open"),
    sqlalchemy.Column("logged_date", sqlalchemy.DateTime, default=sqlalchemy.func.now())
)
# --- END NEW TABLE ---


# --- NEW TABLE FOR CHAMPION NETWORK (IDEA #2) ---
champion_network_table = sqlalchemy.Table(
    "champion_network",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("champion_name", sqlalchemy.String),
    sqlalchemy.Column("champion_email", sqlalchemy.String),
    sqlalchemy.Column("department", sqlalchemy.String),
    # This links the champion to a project
    sqlalchemy.Column("project_name", sqlalchemy.String), 
    sqlalchemy.Column("status", sqlalchemy.String, default="Active")
)
# --- END NEW TABLE ---


# --- NEW TABLE FOR CHANGE HEALTH DASHBOARD (PHASE 3) ---
health_snapshot_table = sqlalchemy.Table(
    "health_snapshot",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    # This is the "Foreign Key" linking to the project
    sqlalchemy.Column("project_id", sqlalchemy.Integer), 
    
    sqlalchemy.Column("log_date", sqlalchemy.String), # We'll store the date as a string

    # --- Lead Indicators (For PMO) ---
    sqlalchemy.Column("readiness_score", sqlalchemy.Integer),    # 1-5 scale
    sqlalchemy.Column("sentiment_score", sqlalchemy.Integer),    # 1-5 scale
    sqlalchemy.Column("manager_confidence", sqlalchemy.Integer), # 1-5 scale

    # --- Lag Indicators (For CEO / ROI) ---
    sqlalchemy.Column("adoption_rate_pct", sqlalchemy.Integer),  # 0-100%
    sqlalchemy.Column("behavior_adoption_pct", sqlalchemy.Integer), # 0-100%
    sqlalchemy.Column("staff_turnover_pct", sqlalchemy.Integer), # 0-100% (for that period)
    
    # --- Context ---
    sqlalchemy.Column("notes", sqlalchemy.String) # e.g., "Sentiment is low due to login bugs"
)
# --- END NEW TABLE ---





# Create the table (and new columns if they don't exist)
metadata.create_all(engine)
