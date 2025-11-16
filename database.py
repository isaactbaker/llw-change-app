# database.py
import sqlalchemy

# Define the database connection
DATABASE_URL = "sqlite:///./change_portfolio_v3.db"
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
    
    sqlalchemy.Column("submission_date", sqlalchemy.DateTime, default=sqlalchemy.func.now())
)

# Create the table (and new columns if they don't exist)
metadata.create_all(engine)