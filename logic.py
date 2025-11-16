# logic.py
import json

# 1. Scoring Logic (This is unchanged)
SCORING_MODEL = {
    "change_type": {"Restructure": 5, "New IT System": 4, "AI Bot": 4, "Process Tweak": 2, "Comms Only": 1},
    "scale": {"250+ people": 3, "50-250 people": 2, "1-50 people": 1},
    "impact_depth": {"A lot of new skills": 4, "A few new steps": 2, "New login only": 1},
    "change_history": {"Failed before": 3, "First time": 1, "Succeeded before": 0}
}

# --- NEW CONSTANT FOR IDEA #3 ---
# Defines the estimated "effort points" per project tier.
# This is for the capacity dashboard.
EFFORT_MAP = {
    "Light Support": 10,
    "Medium Support": 40,
    "Full Support": 100
}
# --- END NEW CONSTANT ---

# --- NEW CONSTANT FOR IDEA #4 ---
# This is the new structured data for the interactive playbooks.
# We will save this to the DB as a JSON string.
PLAYBOOK_TEMPLATES = {
    "Light Support": [
        {"Category": "Comms", "Task": "Draft 'Change-on-a-Page'", "Status": "To Do"},
        {"Category": "Comms", "Task": "Identify Key Audience", "Status": "To Do"},
        {"Category": "Comms", "Task": "Define Key Message (WIIFM)", "Status": "To Do"},
        {"Category": "Comms", "Task": "Select Channel & Timing", "Status": "To Do"},
        {"Category": "Comms", "Task": "Send Communication", "Status": "To Do"}
    ],
    "Medium Support": [
        {"Category": "ADKAR", "Task": "Build Awareness (Comms)", "Status": "To Do"},
        {"Category": "ADKAR", "Task": "Build Desire (WIIFM)", "Status": "To Do"},
        {"Category": "ADKAR", "Task": "Deliver Knowledge (Training)", "Status": "To Do"},
        {"Category": "ADKAR", "Task": "Develop Ability (Practice)", "Status": "To Do"},
        {"Category": "ADKAR", "Task": "Reinforce (Celebrate)", "Status": "To Do"}
    ],
    "Full Support": [
        {"Category": "Sponsor", "Task": "Send the 'Vision' email", "Status": "To Do"},
        {"Category": "Sponsor", "Task": "Attend project kick-off", "Status": "To Do"},
        {"Category": "Sponsor", "Task": "Run 'Crucial Conversations' session", "Status": "To Do"},
        {"Category": "Toolkit", "Task": "Complete Stakeholder Map", "Status": "To Do"},
        {"Category": "Toolkit", "Task": "Complete ADKAR Assessment", "Status": "To Do"},
        {"Category": "Toolkit", "Task": "Establish Change Champion Network", "Status": "To Do"},
        {"Category": "Toolkit", "Task": "Draft Comms & Engagement Plan", "Status": "To Do"},
        {"Category": "Toolkit", "Task": "Draft Training & Support Plan", "Status": "To Do"},
        {"Category": "Toolkit", "Task": "Draft Resistance Management Plan", "Status": "To Do"}
    ]
}
# --- END NEW CONSTANT ---

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

# 3. Triage Function (UPDATED for Idea #3)
def calculate_triage(form_data: dict) -> dict:
    """Calculates score, tier, and effort from form data."""
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

# --- NEW LOGIC FOR IDEA #3 ---
    effort = EFFORT_MAP.get(tier, 0)
    
    # --- NEW LOGIC FOR IDEA #4 ---
    # Get the correct playbook template from our new constant
    playbook_template = PLAYBOOK_TEMPLATES.get(tier, [])
    # Convert the Python list of dicts into a JSON string
    playbook_json_string = json.dumps(playbook_template)
    # --- END NEW LOGIC ---

    # Add all new keys to the returned dictionary
    return {
        "impact_score": score, 
        "change_tier": tier, 
        "effort_score": effort,
        "playbook_data": playbook_json_string # <--- This is the new key
    }