# database.py
import sqlalchemy

# Define the database connection
DATABASE_URL = "sqlite:///./change_portfolio.db"
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Define the table structure (just like your Lovable Table)
change_portfolio_table = sqlalchemy.Table(
    "change_portfolio",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("project_name", sqlalchemy.String),
    sqlalchemy.Column("exec_sponsor", sqlalchemy.String),
    sqlalchemy.Column("change_type", sqlalchemy.String),
    sqlalchemy.Column("scale", sqlalchemy.String),
    sqlalchemy.Column("impact_depth", sqlalchemy.String),
    sqlalchemy.Column("change_history", sqlalchemy.String),
    sqlalchemy.Column("go_live_date", sqlalchemy.String), # Use string for simplicity
    sqlalchemy.Column("impact_score", sqlalchemy.Integer),
    sqlalchemy.Column("change_tier", sqlalchemy.String),
    sqlalchemy.Column("submission_date", sqlalchemy.DateTime, default=sqlalchemy.func.now())
)

# Create the table if it doesn't exist
metadata.create_all(engine)