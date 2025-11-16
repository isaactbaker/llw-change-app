# ai_logic.py
import streamlit as st
from openai import OpenAI
import pandas as pd

# 1. Initialize the API Client
# It automatically reads the API key from st.secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    API_IS_CONFIGURED = True
except Exception as e:
    # This will happen if the secret isn't set
    API_IS_CONFIGURED = False

# 2. Prompt Library
# Storing prompts here makes them easy to edit
PROMPT_FRICTION_ANALYSIS = """
You are an expert Change Management consultant specializing in "Friction & Sludge Audits."
I have provided you with a list of raw, unfiltered "friction notes" logged by staff.
Your task is to analyze all of these notes and generate a "Friction & Sludge" report.

Your report must:
1.  Identify 3-5 major, recurring themes (e.g., "Login & IT Issues," "Confusing Communications," "Process Bottlenecks").
2.  For each theme, provide a 1-2 sentence summary of the core problem.
3.  For each theme, pull 2-3 representative quotes from the notes to use as evidence.
4.  Conclude with a 1-paragraph "Executive Summary" that prioritzes the #1 most urgent theme to address.

Format your entire response in clear, professional Markdown.

Here are the friction notes:
{friction_notes}
"""

PROMPT_SURVEY_ANALYSIS = """
You are a senior analyst on a People & Culture team.
I have provided you with a list of open-ended survey comments from staff about a recent change.
Your task is to analyze these comments and provide a "Sentiment & Thematic Analysis" report.

Your report must:
1.  Provide an overall "Executive Summary" of the general sentiment (e.g., "Overwhelmingly positive," "Mixed but hopeful," "Significant resistance").
2.  Identify 3-4 "Positive Themes" (what staff liked or are excited about). For each, provide 2 representative quotes.
3.  Identify 3-4 "Negative Themes" (key risks, points of confusion, or areas of resistance). For each, provide 2 representative quotes.
4.  Conclude with 3 "Actionable Recommendations" for the Change Manager based on your analysis.

Format your entire response in clear, professional Markdown.

Here are the survey comments:
{survey_comments}
"""

# --- NEW PROMPTS FOR CHAMPION CO-PILOT ---

PROMPT_CHAMPION_KICKOFF = """
You are an expert change manager drafting a communication.
Your task is to draft an inspiring, concise, 200-word kick-off email to our new Change Champions for the '{project_name}' project.

The tone must be:
- Appreciative (thank them for stepping up).
- Clear (state the goal of the network).
- Action-oriented (what is the immediate next step, e.g., 'our first meeting').

Do not use overly complex jargon. Make it human and exciting.
"""

PROMPT_CHAMPION_TALKING_POINTS = """
You are an expert change manager creating a brief for your Change Champions.
Your task is to generate a 1-page "Talking Points" brief for the champions of the '{project_name}' project.

The project's Change Tier is: {change_tier}
The main identified human risk is: {behavioural_barrier}

Based on this context, your brief MUST include:
1.  **Project "Elevator Pitch":** A 1-2 sentence, simple way to describe the project.
2.  **3 Key "What's In It For Me?" (WIIFM) Points:** Why should staff be on board?
3.  **3 "Likely Questions & Simple Answers":** Based on the '{behavioural_barrier}' risk, anticipate 3 tough questions or points of resistance and provide a simple, honest answer for each.

Format the output in clear, professional Markdown.
"""
# --- END NEW PROMPTS ---

# --- NEW PROMPT FOR READINESS DIAGNOSTIC ---
PROMPT_READINESS_PLAN = """
You are a PhD in Applied Behavioural Science, specializing in change management and the COM-B model.
Your task is to generate a 'Change Readiness Interventions Plan' for a project.

Here is the context:
- Project Name: {project_name}
- Low Readiness Groups: {low_readiness_groups}
- Primary Barrier (COM-B Diagnosis): {barrier}
- Key Rumor/Story: {rumor}

Based *only* on this context, generate a full, professional intervention plan. The plan must be formatted in Markdown and must include all of the following sections:

1.  **Strategic Brief:** A 60-second summary translating the diagnosis into a core intervention focus and the critical first action.
2.  **Readiness Root Cause Analysis (COM-B):** A brief analysis explaining *why* the diagnosed barrier ('{barrier}') is the likely root cause for the '{low_readiness_groups}', especially considering the rumor '{rumor}'.
3.  **Intervention Architecture:** A tailored strategy. Based on the '{barrier}' diagnosis, describe the *type* of interventions required (e.g., psychological skills training for 'Capability', removing environmental friction for 'Opportunity', or reframing the narrative for 'Motivation').
4.  **High-Impact Intervention Playbook:** A step-by-step guide for the 2-3 most critical interventions to launch in the next 30 days. Be specific.
5.  **Leadership Communication Cascade:** Pre-scripted talking points for leaders to champion this new intervention plan, ensuring they can confidently explain the 'why'.
6.  **Progress Measurement Loop:** A simple dashboard of 2-3 leading behavioral indicators to track if the interventions are working.
"""
# --- END NEW PROMPT ---


# --- NEW PROMPT FOR COMMS CAMPAIGN ---
PROMPT_COMMS_CAMPAIGN = """
You are an expert in Behavioral Science and Change Management communications.
Your task is to generate a full "Behavioral Communications Campaign Blueprint" based on the user's inputs.

Project Context:
- Project Name: {project_name}
- Key Audience Segments: {audience_segments}
- Master Narrative (Core Message): {narrative}
- Biggest 'Tough Question' Expected: {tough_question}

Your blueprint must be formatted in professional Markdown and include all five of the following sections:

1.  **Audience Psychology X-Ray:** Based on the segments ({audience_segments}), describe their likely psychological reaction (e.g., fears, hopes, 'what's in it for me?').
2.  **The Master Narrative Arc:** Structure a multi-phase campaign (e.g., Phase 1: Why Change?, Phase 2: What's Changing?, Phase 3: How We Get There).
3.  **Multi-Channel Campaign Playbook:** Recommend specific messages for different channels (e.g., Leadership Town Hall, Manager Huddles, Email) for each phase.
4.  **Manager Enablement Toolkit:** Provide 3-4 bulleted talking points and a simple answer to the "Tough Question" ('{tough_question}') for managers to use.
5.  **Feedback & Rumor Mill Protocol:** Suggest 2-3 specific, proactive ways to gather feedback and address rumors.
"""
# --- END NEW PROMPT ---


# 3. API-Calling Functions

def get_api_client():
    """Checks for API key and returns client or None."""
    if not API_IS_CONFIGURED:
        st.error("OpenAI API key is not set. Please add it to your Streamlit secrets.")
        return None
    return client

def call_ai_analysis(prompt_template: str, data_payload: dict, system_prompt: str) -> str:
    """A generic function to call the OpenAI API with a dynamic system prompt."""
    client = get_api_client()
    if client is None:
        return "AI analysis could not be performed. API key is missing."

    try:
        # Format the user-facing prompt
        prompt = prompt_template.format(**data_payload)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt}, # <-- Use the new argument
                {"role": "user", "content": prompt}
            ],
            model="gpt-4-turbo", # Using a strong model
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred during AI analysis: {e}"


# ai_logic.py

def run_friction_analysis(df_friction: pd.DataFrame) -> str:
    """Analyzes friction notes."""
    system_prompt = 'You are an expert Change Management consultant specializing in "Friction & Sludge Audits."'
    notes_string = "\n- ".join(df_friction['friction_note'].tolist())
    payload = {"friction_notes": notes_string}
    
    return call_ai_analysis(PROMPT_FRICTION_ANALYSIS, payload, system_prompt)


def run_survey_analysis(df_survey: pd.DataFrame, column_name: str) -> str:
    """Analyzes survey comments from a specific column."""
    system_prompt = "You are a senior analyst on a People & Culture team."
    if column_name not in df_survey.columns:
        return f"Error: The column '{column_name}' was not found in the uploaded file."

    comments_string = "\n- ".join(df_survey[column_name].dropna().astype(str).tolist())
    payload = {"survey_comments": comments_string}
    
    return call_ai_analysis(PROMPT_SURVEY_ANALYSIS, payload, system_prompt)


def run_champion_kickoff_email(project_name: str) -> str:
    """Generates a champion kick-off email for a project."""
    system_prompt = "You are an expert change manager drafting an inspiring and clear communication."
    payload = {"project_name": project_name}
    return call_ai_analysis(PROMPT_CHAMPION_KICKOFF, payload, system_prompt)


def run_champion_talking_points(project_name: str, change_tier: str, behavioural_barrier: str) -> str:
    """Generates champion talking points based on project context."""
    system_prompt = "You are an expert change manager creating a strategic brief for your Change Champions."
    payload = {
        "project_name": project_name,
        "change_tier": change_tier,
        "behavioural_barrier": behavioural_barrier
    }
    return call_ai_analysis(PROMPT_CHAMPION_TALKING_POINTS, payload, system_prompt)

def run_readiness_diagnostic(project_name: str, low_readiness_groups: list, barrier: str, rumor: str) -> str:
    """GenerTATES a change readiness intervention plan."""
    system_prompt = "You are a PhD in Applied Behavioural Science, specializing in change management and the COM-B model."
    payload = {
        "project_name": project_name,
        "low_readiness_groups": ", ".join(low_readiness_groups),
        "barrier": barrier,
        "rumor": rumor
    }
    return call_ai_analysis(PROMPT_READINESS_PLAN, payload, system_prompt)


# --- NEW FUNCTION FOR COMMS CAMPAIGN ---
def run_comms_campaign_generator(project_name: str, audience_segments: list, narrative: str, tough_question: str) -> str:
    """Generates a full behavioral communications campaign plan."""
    system_prompt = "You are a comms expert grounded in behavioral science."
    payload = {
        "project_name": project_name,
        "audience_segments": ", ".join(audience_segments),
        "narrative": narrative,
        "tough_question": tough_question
    }
    return call_ai_analysis(PROMPT_COMMS_CAMPAIGN, payload, system_prompt)
# --- END NEW FUNCTION ---