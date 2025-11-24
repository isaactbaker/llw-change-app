# logic.py
import json

# 1. Configuration Data (The "Brain")

# Budget estimations per head (simplified for demo)
COST_PER_HEAD = {
    "Global Executive": 5000, # High touch, external vendors
    "Senior Leader": 2500,
    "People Leader": 1000,
    "Technical Specialist": 2000, # Technical bootcamps
    "General Workforce": 100 # Scalable licensing
}

# --- NEW CONFIGURATION DATA ---
# QBE AI PRINCIPLES (1.1)
QBE_AI_PRINCIPLES = [
    "Fairness (Prevent Bias/Discrimination)",
    "Privacy (Data Safeguarding)",
    "Transparency (Disclosure of AI Use)",
    "Explainability (Intelligibility of Outcomes)",
    "Accountability (Human Oversight)",
    "Benefit & Safety (Prevent Harm)"
]

# NEW: Mapping QBE Regions to ISO Country Codes for the Heatmap
REGION_ISO_MAP = {
    "AUSPAC": ["AUS", "NZL"],
    "North America": ["USA", "CAN"],
    "Europe": ["GBR", "FRA", "DEU", "ITA", "ESP"],
    "EO (Equal Opportunities)": ["PHL", "IND"], 
    "Global": [] 
}

# NEW: Default Vendors (Pre-seeding)
DEFAULT_VENDORS = [
    # ADDED compliance_rating & data_residency_cert fields
    {"vendor_name": "Gartner", "specialty": "Strategy", "avg_daily_rate": 5000, "performance_rating": 5, "compliance_rating": "Green", "data_residency_cert": "Global"},
    {"vendor_name": "Microsoft", "specialty": "Technical", "avg_daily_rate": 3500, "performance_rating": 4, "compliance_rating": "Green", "data_residency_cert": "EU-GDPR"},
    {"vendor_name": "Internal L&D", "specialty": "Soft Skills", "avg_daily_rate": 500, "performance_rating": 3, "compliance_rating": "Green", "data_residency_cert": "Internal"},
    {"vendor_name": "LinkedIn Learning", "specialty": "General", "avg_daily_rate": 50, "performance_rating": 4, "compliance_rating": "Yellow", "data_residency_cert": "None"},
    {"vendor_name": "NeuroLeadership Inst", "specialty": "Culture", "avg_daily_rate": 4000, "performance_rating": 5, "compliance_rating": "Green", "data_residency_cert": "AUS-Privacy"},
]

# The Logic Matrix: Mapping Audience + Maturity to a Pathway
# This mimics the "Curation" role of the job description
PATHWAY_LOGIC = {
    "Global Executive": {
        "Skeptic": "The AI Visionary Program",
        "Observer": "The AI Visionary Program",
        "Experimenter": "Strategic AI Governance",
        "Adopter": "Leading Disruption"
    },
    "Senior Leader": {
        "Skeptic": "Leading through Uncertainty",
        "Observer": "AI Strategy Fundamentals",
        "Experimenter": "Operational AI Scaling",
        "Adopter": "Transformational Leadership"
    },
    "People Leader": {
        "all": "Managing AI-Augmented Teams" # Default for mid-level
    },
    "Technical Specialist": {
        "all": "The AI Builder Bootcamp" # Technical focus
    },
    "General Workforce": {
        "Skeptic": "The Resilient Human (Soft Skills)",
        "Observer": "AI Literacy 101",
        "Experimenter": "Everyday Innovator (Prompting)",
        "Adopter": "Process Automation Masterclass"
    }
}

# Detailed Program Descriptions (The "Curated Resources")
LEARNING_PATHWAYS = {
    "The AI Visionary Program": """
    ### 🚀 Recommended Pathway: The AI Visionary Program
    **Target Audience:** Executives & Skeptics
    **Goal:** Shift mindset from "Risk Aversion" to "Strategic Opportunity."
    
    **Curated Vendor Strategy:**
    * **Primary:** External Thought Leader (e.g., Gartner/Forrester briefing).
    * **Format:** 1-Day Executive Offsite.
    
    **Key Modules:**
    1.  **AI Economics:** How AI shifts the P&L of Insurance.
    2.  **The Ethical Leader:** Navigating bias and trust in automated claims.
    3.  **Strategic Forecasting:** 5-year horizon scanning.
    """,
    
    "The Resilient Human (Soft Skills)": """
    ### 🧠 Recommended Pathway: The Resilient Human
    **Target Audience:** General Workforce (Skeptics/Anxious)
    **Goal:** Build psychological safety and emphasize human value in the loop.
    
    **Curated Vendor Strategy:**
    * **Primary:** Internal L&D + Psychology Vendor (e.g., NeuroLeadership Inst).
    * **Format:** Workshop Series + Coaching Circles.
    
    **Key Modules:**
    1.  **Thriving in Ambiguity:** Managing change fatigue.
    2.  **Critical Thinking:** Why AI needs a human auditor.
    3.  **Empathy & Ethics:** Skills AI cannot replace.
    """,
    
    "The AI Builder Bootcamp": """
    ### 🛠️ Recommended Pathway: The AI Builder Bootcamp
    **Target Audience:** Technical Specialists
    **Goal:** Rapid upskilling in LLM Ops and Secure Architecture.
    
    **Curated Vendor Strategy:**
    * **Primary:** Microsoft / Tech Vendor.
    * **Format:** 5-Day Hackathon + Certification.
    
    **Key Modules:**
    1.  **Secure AI Architecture:** Privacy by design in QBE systems.
    2.  **Advanced RAG:** Retrieval Augmented Generation.
    3.  **Copilot Extensions:** Building custom plugins.
    """,
    
    "Everyday Innovator (Prompting)": """
    ### 💡 Recommended Pathway: The Everyday Innovator
    **Target Audience:** General Workforce (Experimenters)
    **Goal:** Productivity gains and grassroots innovation.
    
    **Curated Vendor Strategy:**
    * **Primary:** Scalable Learning Platform (LinkedIn Learning / Udemy).
    * **Format:** Self-Paced + "Lunch & Learn" Showcases.
    
    **Key Modules:**
    1.  **Prompt Engineering 101:** Getting better answers.
    2.  **Automating the Mundane:** freeing up time for high-value work.
    3.  **Data Privacy:** What NOT to put in the prompt.
    """
}

# Default fallback for pathways not explicitly defined above
DEFAULT_PATHWAY = """
### 📈 Recommended Pathway: QBE AI Core Skills
**Goal:** foundational literacy and alignment with QBE AI Strategy.
**Vendor:** Internal Digital Academy.
"""


# NEW: Gap Calculation Helper
def calculate_behavioural_gap(baseline, target):
    """Returns the 'Gap Size' and a strategic tag."""
    delta = target - baseline
    if delta >= 5:
        return delta, "CRITICAL SHIFT (Transformation Required)"
    elif delta >= 3:
        return delta, "SIGNIFICANT SHIFT (Coaching Required)"
    else:
        return delta, "INCREMENTAL SHIFT (Upskilling Required)"
    


# --- NEW LOGIC FUNCTION (1.2) ---
def check_compliance_risk(region: str, vendor_name: str) -> bool:
    """Checks if the vendor is compliant for the target region."""
    import pandas as pd
    from database import engine

    try:
        vendor_df = pd.read_sql_table("vendor_registry", engine)
        vendor_row = vendor_df[vendor_df['vendor_name'] == vendor_name].iloc[0]
        
        vendor_cert = vendor_row['data_residency_cert']
        compliance_rating = vendor_row['compliance_rating']
        
        if compliance_rating == "Red":
            return "Major Risk: Vendor is flagged as high-risk."
        
        # Simple Logic for Demonstration (Must refine in real-world)
        if region == "Europe" and "GDPR" not in vendor_cert:
            return "RISK: European program using non-GDPR certified vendor."
        
        if region == "AUSPAC" and "Privacy" not in vendor_cert and vendor_cert != "Internal":
            return "RISK: AUSPAC program using vendor without local privacy certification."

        return None # No specific risk found

    except:
        return None # Default to no risk if DB fails


def curate_pathway(form_data: dict) -> dict:
    """
    The 'Intelligence Engine' that maps inputs to a recommended strategy.
    """
    audience = form_data["audience_level"]
    maturity = form_data["current_maturity"]
    cohort_size_str = form_data["cohort_size"] # e.g. "1-20"
    
    # 1. Determine Pathway Name
    # Check specialized logic first, else fall back
    if audience in PATHWAY_LOGIC:
        # If the audience dict has specific maturity keys (like Execs)
        if isinstance(PATHWAY_LOGIC[audience], dict):
            program_name = PATHWAY_LOGIC[audience].get(maturity, "QBE AI Core Skills")
        else:
            # If it's a flat string (like Technical Specialist) - handle "all" key
            program_name = PATHWAY_LOGIC[audience].get("all", "QBE AI Core Skills")
    else:
        program_name = "QBE AI Core Skills"

    # 2. Get Description
    program_description = LEARNING_PATHWAYS.get(program_name, DEFAULT_PATHWAY)
    
    # 3. Identify Vendor (Simple extraction for the DB field)
    # In a real app, this would be a separate lookup
    if "Visionary" in program_name:
        vendor = "Gartner / External"
    elif "Builder" in program_name:
        vendor = "Microsoft / Tech"
    elif "Resilient" in program_name:
        vendor = "Internal L&D / Psych"
    else:
        vendor = "Internal / Platform"

    # 4. Calculate Urgency Score (0-100)
    # Higher seniority + Lower Maturity = Higher Urgency/Risk
    urgency = 50 # Base
    if "Exec" in audience or "Senior" in audience:
        urgency += 30
    if maturity == "Skeptic" or maturity == "Observer":
        urgency += 20
    
    # 5. Estimate Budget
    # Parse size string to an average integer
    if "1-20" in cohort_size_str: count = 15
    elif "20-100" in cohort_size_str: count = 60
    else: count = 150
    
    cost_basis = COST_PER_HEAD.get(audience, 100)
    budget = count * cost_basis

    return {
        "urgency_score": urgency,
        "recommended_pathway": program_name,
        "recommended_vendor": vendor,
        "program_description": program_description,
        "estimated_budget": budget
    }
