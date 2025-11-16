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


# 3. API-Calling Functions

def get_api_client():
    """Checks for API key and returns client or None."""
    if not API_IS_CONFIGURED:
        st.error("OpenAI API key is not set. Please add it to your Streamlit secrets.")
        return None
    return client

def call_ai_analysis(prompt_template: str, data_payload: str) -> str:
    """A generic function to call the OpenAI API."""
    client = get_api_client()
    if client is None:
        return "AI analysis could not be performed. API key is missing."

    try:
        # Format the prompt
        prompt = prompt_template.format(**data_payload)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful expert consultant."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-5-mini-2025-08-07", # You can change this to gpt-3.5-turbo for speed
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred during AI analysis: {e}"


def run_friction_analysis(df_friction: pd.DataFrame) -> str:
    """Analyzes friction notes."""
    # Convert dataframe to a simple string
    notes_string = "\n- ".join(df_friction['friction_note'].tolist())
    payload = {"friction_notes": notes_string}
    
    return call_ai_analysis(PROMPT_FRICTION_ANALYSIS, payload)


def run_survey_analysis(df_survey: pd.DataFrame, column_name: str) -> str:
    """Analyzes survey comments from a specific column."""
    if column_name not in df_survey.columns:
        return f"Error: The column '{column_name}' was not found in the uploaded file."

    # Convert the specified column to a simple string
    comments_string = "\n- ".join(df_survey[column_name].dropna().astype(str).tolist())
    payload = {"survey_comments": comments_string}
    
    return call_ai_analysis(PROMPT_SURVEY_ANALYSIS, payload)