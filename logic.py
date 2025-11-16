# logic.py

# 1. Scoring Logic (This is unchanged)
SCORING_MODEL = {
    "change_type": {"Restructure": 5, "New IT System": 4, "AI Bot": 4, "Process Tweak": 2, "Comms Only": 1},
    "scale": {"250+ people": 3, "50-250 people": 2, "1-50 people": 1},
    "impact_depth": {"A lot of new skills": 4, "A few new steps": 2, "New login only": 1},
    "change_history": {"Failed before": 3, "First time": 1, "Succeeded before": 0}
}

# 2. Toolkit Content (NEW, UPGRADED VERSION)
TOOLKITS = {
    "Light Support": """
    ### TIER 1: LIGHT SUPPORT
    This project primarily requires clear and consistent communication.
    
    **Your 'Change-on-a-Page' Template:**
    * **Project Goal:** (What is the 1-sentence goal?)
    * **Audience:** (Who needs to know?)
    * **Key Message (WIIFM):** (What's in it for them? Why should they care?)
    * **Channel:** (How will you tell them? e.g., Email, Team Meeting)
    * **Timing:** (When?)
    """,
    "Medium Support": """
    ### TIER 2: MEDIUM SUPPORT
    This project requires structured change management. We will use an **ADKAR-based** approach (which Ben is an expert in).
    
    **Your 'ADKAR Plan' Template:**
    * **Awareness:** How will you build awareness of the *need* for this change?
    * **Desire:** How will you address 'What's in it for me?' (WIIFM) to build motivation?
    * **Knowledge:** What training is needed? How will people learn *how* to do it?
    * **Ability:** How will you provide practice, support, and time to build new skills?
    * **Reinforcement:** How will you celebrate success and make the change stick?
    """,
    "Full Support": """
    ### TIER 3: FULL SUPPORT
    This is a high-impact, high-risk project. I (Dr. Baker) will contact you for a full discovery and planning session.
    
    **Your #1 priority is Sponsor Alignment.** A project of this scale will fail without an active, visible sponsor.
    
    **Sponsor Action Checklist (For your Exec Sponsor):**
    * [ ] 1. Send the "Vision" email (we will draft this) to all impacted staff.
    * [ ] 2. Attend the project kick-off and *personally* state why this is important.
    * [ ] 3. Allocate 1 hour/month for a "Crucial Conversations" session to address resistance.
    
    **Your Toolkit Checklist:**
    * [ ] 1. Stakeholder Map & ADKAR Assessment
    * [ ] 2. Change Champion Network Plan
    * [ ] 3. Detailed Comms & Engagement Plan
    * [ ] 4. Training & Support Plan
    * [ ] 5. Feedback & Resistance Management Plan
    """
}

# 3. Triage Function (This is unchanged)
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