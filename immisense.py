
import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv


from agno.agent import Agent
from agno.team import Team
from agno.models.google import Gemini
from agno.tools.exa import ExaTools

from visa_utils import VISA_DESCRIPTIONS, ASSESSMENT_QUESTIONS



load_dotenv()

st.set_page_config(
    page_title="ImmiSense AI",
    page_icon="✈️",
    layout="wide"
)


# --- AGENT & TEAM INITIALIZATION (WITH CACHING) ---
@st.cache_resource
def load_immigrify_team():
    """
    Initializes and returns the complete agno Team.
    """
    print("Initializing AI Team... (This should only run once)")
    # Configuration
    google_api_key = os.getenv("GOOGLE_API_KEY")
    exa_api_key = os.getenv("EXA_API_KEY")

    if not google_api_key or not exa_api_key:
        st.error("API keys are not found. Please check your .env file.")
        st.stop()
    
    coordinator_llm = Gemini(id="gemini-2.5-pro", api_key=google_api_key)
    worker_llm = Gemini(id="gemini-2.5-flash", api_key=google_api_key)
    exa_tools_instance = ExaTools(api_key=exa_api_key)

    # --- Agent and Team definitions go here ---
    ProfileParser = Agent(name="ProfileParser", 
                          model=worker_llm, 
                          role="User Profile JSON Extractor", 
                          instructions=
                          ["Your sole responsibility is to read the user's query and extract key information.", 
                           "You MUST output your findings as a single, valid JSON object and nothing else.", 
                           "The JSON object must contain keys: 'full_name', 'age', 'nationality', 'visa_category', and other relevant profile details.", 
                           "If a value is not found, use `null`. Your entire response MUST be only the JSON object."
                           ],
                           retries=2,)
    
    VisaResearcher = Agent(name="VisaResearcher", 
                           model=worker_llm, 
                           tools=[exa_tools_instance], 
                           role="Visa Requirements Specialist", 
                           instructions=[
                               "You will be given a specific U.S. visa category (e.g., 'H-1B').", 
                               "Your only task is to use the search tool to find the primary eligibility requirements from official U.S. government sources (uscis.gov, travel.state.gov).", 
                               "You MUST output the requirements as a single, valid JSON object with a single key, 'visa_requirements', which holds a list of the requirements.", 
                               "Your entire response MUST be only the JSON object."
                               ],
                               retries=2,
                               )
    
    ScoringEngine = Agent(name="ScoringEngine", 
                          model=worker_llm, 
                          role="Eligibility Scoring Analyst", 
                          instructions=["You will receive a JSON object containing a 'user_profile' and 'visa_requirements'.", 
                                        "Your task is to logically compare the user's profile against each requirement.", 
                                        "You MUST output your analysis as a single, valid JSON object.", 
                                        "The JSON object must contain keys: 'overall_score' (number 0-100), and 'score_breakdown' (an object detailing the score for each category).", 
                                        "Your entire response MUST be only the JSON object."],
                                        retries=2,
                                        )
    
    RecommendationAgent = Agent(name="RecommendationAgent", 
                            model=worker_llm, 
                            role="Strategic Immigration Advisor", 
                            instructions=["You will receive a JSON object containing 'user_profile', 'visa_requirements', and 'scoring_data'.", 
                                          "Your task is to provide expert strategic advice based on this data.", 
                                          "Analyze the score breakdown to identify the strongest and weakest points of the user's case.", 
                                          "You MUST output your advice as a single, valid JSON object.", 
                                          "The JSON object must contain these keys: 'summary' (a brief overview), 'key_considerations' (a list of strengths and weaknesses), 'actionable_steps' (a list of concrete next steps), and 'alternative_pathways' (a list of other potential visa options, if any).", 
                                          "Your entire response MUST be only the JSON object."], 
                                          retries=2,
                                         )
    
    ReportGenerator = Agent(name="ReportGenerator", 
                            model=coordinator_llm, role="Final Report Compiler", 
                            instructions=["Your role is to act as a compiler. You will receive a single JSON object containing all assessment data: 'profile', 'requirements', 'scoring', and now 'recommendations'.", 
                                          "Your final task is to synthesize all this structured information into a single, comprehensive, and well-structured user-facing report in Markdown format.", 
                                          "The report must be written from the perspective of 'ImmiSense' and MUST include distinct sections for: Applicant Profile, Eligibility Assessment, and Strategic Recommendations.", 
                                          "Use the data from the 'recommendations' JSON to populate the final section of the report."], 
                                          markdown=True, 
                                          retries=2,
                                          stream=True)

    # Team Definition
    immigrify_team = Team(
        name="ImmigrifyTeam",
        mode="collaborate", # Using coordinate for predictable, sequential workflow
        members=[ProfileParser, VisaResearcher, ScoringEngine, RecommendationAgent, ReportGenerator],
        model=coordinator_llm,
        instructions=[
            "You are an expert team of immigration analysts that assesses a user's eligibility for a U.S. visa.",
            "Your goal is to produce a comprehensive eligibility and recommendation report.",
            "You MUST follow these steps in a strict sequence:",
            "1. **Parse Profile:** Use the `ProfileParser` to extract the user's details into a structured JSON format.",
            "2. **Research Requirements:** Use the `VisaResearcher`, providing it with the `visa_category` from the parsed profile, to get the official visa requirements in JSON format.",
            "3. **Score Eligibility:** Use the `ScoringEngine`. You must provide it with both the structured profile from step 1 and the visa requirements from step 2.",
            "4. **Generate Recommendations:** Use the `RecommendationAgent`. You must provide it with all previously gathered data (the profile, requirements, and score) to generate strategic advice in JSON format.",
            "5. **Generate Final Report:** Use the `ReportGenerator`. You must provide it with all information from all previous steps (profile, requirements, score, and recommendations) to create the final, user-facing report.",
            "The final output delivered to the user must be the complete, polished report from the `ReportGenerator`."
        ],
        enable_agentic_context=True,
    markdown=True,
    debug_mode=True,
    show_members_responses=True,
    )
    return immigrify_team

# --- Load the AI team ---
try:
    team = load_immigrify_team()
except Exception as e:
    st.error(f"Failed to initialize the AI Team. Please check your setup. Error: {e}")
    st.stop()


# --- UI & APP LOGIC ---

# Data Dictionaries
GOAL_TO_VISA_MAPPING = {
    "Select a Goal...": [], "Work in the U.S.": ["H-1B", "L-1", "O-1", "TN", "H-2A/H-2B", "P Visas", "R-1", "EB-1", "EB-2", "EB-3"],
    "Study or Conduct Research": ["F-1", "J-1", "M-1"], "Join Family in the U.S.": ["K-1", "K-3", "IR Visas", "F Visas"],
    "Invest in a U.S. Business": ["EB-5"], "Visit for a Short Period": ["B-1", "B-2"], "Transit or Specialized Travel": ["C", "I", "D"],
}

# Session State Initialization
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'final_report' not in st.session_state:
    st.session_state.final_report = None

# Navigation Functions
def go_to_home(): st.session_state.page = 'Home'
def go_to_profile(): st.session_state.page = 'Profile'
def go_to_assessment():
    st.session_state.final_report = None
    st.session_state.page = 'Assessment'

# Sidebar Navigation
with st.sidebar:
    st.header("Menu")
    st.button("🏠 Home", on_click=go_to_home, use_container_width=True)
    st.button("👤 My Profile", on_click=go_to_profile, use_container_width=True)
    st.button("🚀 Run New Assessment", on_click=go_to_assessment, use_container_width=True)
    st.info("💡 A complete profile enables more accurate AI analysis!")

# --- Main Page Rendering Logic ---

if st.session_state.page == 'Home':
    st.title("Welcome to ImmiSense ✈️")
    st.subheader("Your AI-Powered U.S. Immigration Eligibility Agent")
    st.markdown("""
    Get instant, personalized immigration assessments powered by advanced AI.
    - **Smart Analysis:** AI agents analyze your profile against official requirements.
    - **Detailed Scoring:** Get comprehensive eligibility scores and recommendations.
    - **Strategic Guidance:** Receive actionable steps for your immigration journey.
    """)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Build My Profile First"): go_to_profile()
    with col2:
        if st.button("⚡ Start a Quick Assessment"): go_to_assessment()

elif st.session_state.page == 'Profile':
    st.header("👤 My Profile")
    st.write("Please fill out all fields in this comprehensive profile to enable our AI to perform the most accurate assessment.")

    with st.form("profile_form"):
        # PERSONAL 
        st.header("Personal Factors")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name", st.session_state.user_profile.get("full_name", ""))
            age = st.number_input("Age", 1, 120, st.session_state.user_profile.get("age", 30))
            language_proficiency = st.multiselect("Language Proficiency", ["English", "Spanish", "French", "German", "Mandarin", "Other"], default=st.session_state.user_profile.get("language_proficiency", []))
        with col2:
            highest_degree = st.selectbox("Highest Degree", ["Select...", "High School Diploma", "Bachelor's Degree", "Master's Degree", "PhD"], index=0)
            field_of_study = st.text_input("Field of Study", st.session_state.user_profile.get("field_of_study", ""))
            years_of_experience = st.number_input("Years of Professional Experience", 0, 60, st.session_state.user_profile.get("years_of_experience", 5))
        
        # FINANCIAL 
        st.header("Financial Factors")
        col3, col4 = st.columns(2)
        with col3:
            annual_income = st.number_input("Current Annual Income (USD)", 0, 10000000, st.session_state.user_profile.get("annual_income", 50000), step=1000)
            liquid_assets = st.number_input("Total Liquid Assets (USD)", 0, 100000000, st.session_state.user_profile.get("liquid_assets", 20000), step=1000)
        with col4:
            sponsorship_status = st.selectbox("Sponsorship Status", ["Select...", "Seeking sponsorship", "Have a job offer/sponsorship", "Not applicable"], index=0)

        # LEGAL & COUNTRY
        st.header("Legal & Country-Specific Factors")
        col5, col6 = st.columns(2)
        with col5:
            nationality = st.text_input("Country of Nationality", st.session_state.user_profile.get("nationality", ""))
            birth_country = st.text_input("Country of Birth", st.session_state.user_profile.get("birth_country", ""))
            previous_denials = st.radio("Have you ever had a U.S. visa application denied?", ["No", "Yes"], index=0, horizontal=True)
        with col6:
            current_location = st.text_input("Current Country of Residence", st.session_state.user_profile.get("current_location", ""))
            current_us_status = st.text_input("Current U.S. Immigration Status (if any, otherwise type N/A)", st.session_state.user_profile.get("current_us_status", ""))
            criminal_history = st.radio("Do you have a criminal history?", ["No", "Yes"], index=0, horizontal=True)
        
        submitted = st.form_submit_button("Save Complete Profile")
        if submitted:
            
            profile_data = {
                "Full Name": full_name, "Age": age, "Language Proficiency": language_proficiency,
                "Highest Degree": highest_degree, "Field of Study": field_of_study, "Years of Professional Experience": years_of_experience,
                "Annual Income (USD)": annual_income, "Liquid Assets (USD)": liquid_assets, "Sponsorship Status": sponsorship_status,
                "Country of Nationality": nationality, "Country of Birth": birth_country, "Previous Visa Denials": previous_denials,
                "Current Country of Residence": current_location, "Current U.S. Status": current_us_status, "Criminal History": criminal_history,
            }

            # Check for empty fields
            missing_fields = []
            for field, value in profile_data.items():
                if isinstance(value, str) and not value.strip():
                    missing_fields.append(field)
                elif isinstance(value, list) and not value:
                    missing_fields.append(field)
                elif value in ["Select...", None]:
                    missing_fields.append(field)
            
            if missing_fields:
                st.error(f"Please fill out all required fields. The following fields are missing:\n\n- " + "\n- ".join(missing_fields))
            else:
                # If validation passes, save the data
                st.session_state.user_profile = {
                    "full_name": full_name, "age": age, "language_proficiency": language_proficiency,
                    "highest_degree": highest_degree, "field_of_study": field_of_study, "years_of_experience": years_of_experience,
                    "annual_income_usd": annual_income, "liquid_assets_usd": liquid_assets, "sponsorship_status": sponsorship_status,
                    "nationality": nationality, "birth_country": birth_country, "previous_visa_denials": previous_denials,
                    "current_residence": current_location, "current_us_status": current_us_status, "criminal_history": criminal_history,
                }
                st.success("Your comprehensive profile has been saved successfully!")

    if st.session_state.user_profile:
        st.write("---")
        st.subheader("Current Saved Profile")
        st.json(st.session_state.user_profile)

elif st.session_state.page == 'Assessment':
    st.header("Complete Assessment")
    # ... The rest of the assessment and report logic remains unchanged ...
    if not st.session_state.user_profile:
        st.warning("Please fill out and save your profile via the 'My Profile' page first.")
        st.stop()
    if st.session_state.final_report is None:
        st.header("Select Your Goal and Visa")
        selected_goal = st.selectbox("What is your primary immigration goal?", list(GOAL_TO_VISA_MAPPING.keys()))
        if selected_goal != "Select a Goal...":
            possible_visas = GOAL_TO_VISA_MAPPING[selected_goal]
            selected_visa = st.selectbox("Select the specific Visa Category", possible_visas)
            description = VISA_DESCRIPTIONS.get(selected_visa, "No description available.")
            st.info(f"**About the {selected_visa} Visa:** {description}")
            questions = ASSESSMENT_QUESTIONS.get(selected_visa, [f"Please describe your plans and qualifications for the {selected_visa} visa."])
            with st.form("assessment_form"):
                st.header("Answer Assessment Questions")
                assessment_answers = {q: st.text_area(q, key=f"q_{i}", height=150) for i, q in enumerate(questions)}
                assessment_submitted = st.form_submit_button("Submit & Run AI Analysis")
                if assessment_submitted:
                    with st.spinner("Processing with our AI agent team... This may take a moment."):
                        profile_details = "\n".join([f"- {k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.user_profile.items()])
                        answer_details = "\n".join([f"- Question: {q}\n- Answer: {a}" for q, a in assessment_answers.items()])
                        final_user_query = f"## User Profile:\n{profile_details}\n\n## Assessment for Visa Category: {selected_visa}\n{answer_details}\n\n## Task:\nProvide a comprehensive eligibility report, score, and recommendations."
                        final_report = team.run(final_user_query)
                        st.session_state.final_report = final_report.content
                        st.rerun()
    else:
        st.header("Your ImmiSense Report")
        st.markdown(st.session_state.final_report)
        if st.button("Start Another Assessment"):
            go_to_assessment()