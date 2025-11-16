# logic.py

# 1. Scoring Logic
SCORING_MODEL = {
    "change_type": {"Restructure": 5, "New IT System": 4, "AI Bot": 4, "Process Tweak": 2, "Comms Only": 1},
    "scale": {"250+ people": 3, "50-250 people": 2, "1-50 people": 1},
    "impact_depth": {"A lot of new skills": 4, "A few new steps": 2, "New login only": 1},
    "change_history": {"Failed before": 3, "First time": 1, "Succeeded before": 0}
}

# 2. Toolkit Content (lives inside your app)
TOOLKITS = {
    "Light Support": """
    ## TIER 1: LIGHT SUPPORT
    This project is 'Light Support.' Here is your 'Change-on-a-Page' template...
    (Your full text here)
    """,
    "Medium Support": """
    ## TIER 2: MEDIUM SUPPORT
    This project is 'Medium Support.' This means I am available for coaching...
    (Your full text here)
    """,
    "Full Support": """
    ## TIER 3: FULL SUPPORT
    This project is 'Full Support.' As this is a high-impact project, I (Dr. Baker) will contact you...
    (Your full text here)
    """
}

# 3. Triage Function
def calculate_triage(form_data: dict) -> dict:
    """Calculates score and tier from form data."""
    score = 0
    score += SCORING_MODEL["change_type"].get(form_data["change_type"], 0)
    score += SCORING_MODEL["scale"].get(form_data["scale"], 0)
    score += SCORING_MODEL["impact_depth"].get(form_data["impact_depth"], 0)
    score += SCORING_MODEL["change_history"].get(form_data["change_history"], 0)

    tier = "Light Support"
    if score >= 11:
        tier = "Full Support"
    elif score >= 6:
        tier = "Medium Support"

    return {"impact_score": score, "change_tier": tier}