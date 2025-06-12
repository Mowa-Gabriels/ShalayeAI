from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.exa import ExaTools
from PIL import Image
from agent_task.agent_instructions import *
from dotenv import load_dotenv
import streamlit as st
import os,tempfile,re,time 
from shalaye_utils import optimize_image, extract_scores, extract_risks, plot_parameter_scores 


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")


def create_shalaye_agent() -> Agent:
    """
    Creates the ShalayeAI agent.

    Args:
        gemini_api_key: The API key for the Gemini LLM.
        exa_api_key: The API key for the Exa search engine.

    Returns:
        An Agno Agent instance.
    """
    tools = [ExaTools(api_key=EXA_API_KEY)]

    shalaye_agent = Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=GOOGLE_API_KEY),
        tools=tools,
        name="ShalayeAI",
        description=agent_description,
        instructions=INSTRUCTIONS,
        markdown=True,
    )
    return shalaye_agent

def create_followup_agent() -> Agent:
    tools = [ExaTools(api_key=EXA_API_KEY)]

    followup_agent = Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=GOOGLE_API_KEY),
        tools=tools,
        name="ShalayeAI",
        description=followup_agent_description,
        instructions=FOLLOWUP_INSTRUCTIONS,
        markdown=True,
    )
    return followup_agent


def optimize_image(image: Image.Image) -> Image.Image:
    """
    Optimizes an image for analysis by resizing and converting it to JPEG.

    Args:
        image: A PIL Image object.

    Returns:
        An optimized PIL Image object.
    """
    max_size = (720, 720) 
    image.thumbnail(max_size)
    return image


def initialize_user_profile():
    """Initialize user profile in session state if not exists"""
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'age_range': '',
            'gender': '',
            'weight_kg': '',
            'height_cm': '',
            'activity_level': '',
            'health_goals': [],
            'dietary_preferences': [],
            'allergies': '',
            'health_conditions': [],
            'medications': '',
            'pregnancy_status': '',
            'profile_complete': False
        }


def profile_setup_page():
    """Render the profile setup page"""
    st.title("👨🏻‍💼📝Health Profile Setup")
    
    st.markdown("""
    <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="color: #263e73; margin-top: 0;">Why Personal Information?</h4>
        <p style="color: #555; margin-bottom: 0;">
            Your personal health profile helps ShalayeAI provide personalized recommendations 
            tailored to your specific needs, goals, and health conditions. All information is 
            kept private and used only for analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Basic Information")
            age_range = st.selectbox(
                "Age Range *",
                ["", "18-25", "26-35", "36-45", "46-55", "56-65", "65+"],
                index=0 if not st.session_state.user_profile['age_range'] else 
                ["", "18-25", "26-35", "36-45", "46-55", "56-65", "65+"].index(st.session_state.user_profile['age_range'])
            )
            
            gender = st.selectbox(
                "Gender *",
                ["", "Male", "Female", "Prefer not to say"],
                index=0 if not st.session_state.user_profile['gender'] else 
                ["", "Male", "Female", "Prefer not to say"].index(st.session_state.user_profile['gender'])
            )
            
            weight_kg = st.number_input(
                "Weight (kg)", 
                min_value=0.0, 
                max_value=300.0, 
                value=float(st.session_state.user_profile['weight_kg']) if st.session_state.user_profile['weight_kg'] else 0.0,
                help="Optional - helps calculate nutritional needs"
            )
            
            height_cm = st.number_input(
                "Height (cm)", 
                min_value=0.0, 
                max_value=250.0, 
                value=float(st.session_state.user_profile['height_cm']) if st.session_state.user_profile['height_cm'] else 0.0,
                help="Optional - helps calculate BMI and nutritional needs"
            )
            
            activity_level = st.selectbox(
                "Activity Level *",
                ["", "Sedentary (little/no exercise)", "Lightly Active (light exercise 1-3 days/week)", 
                 "Moderately Active (moderate exercise 3-5 days/week)", "Very Active (hard exercise 6-7 days/week)", 
                 "Extremely Active (very hard exercise, physical job)"],
                index=0 if not st.session_state.user_profile['activity_level'] else 
                ["", "Sedentary (little/no exercise)", "Lightly Active (light exercise 1-3 days/week)", 
                 "Moderately Active (moderate exercise 3-5 days/week)", "Very Active (hard exercise 6-7 days/week)", 
                 "Extremely Active (very hard exercise, physical job)"].index(st.session_state.user_profile['activity_level'])
            )

        with col2:
            st.subheader("🎯 Goals & Preferences")
            health_goals = st.multiselect(
                "Health Goals",
                ["Weight Loss", "Weight Gain", "Muscle Building", "Heart Health", 
                 "Immune Support", "Energy Boost", "Better Sleep", "Digestive Health", 
                 "Bone Health", "Mental Clarity", "Skin Health"],
                default=st.session_state.user_profile['health_goals']
            )
            
            dietary_preferences = st.multiselect(
                "Dietary Preferences/Restrictions",
                ["None", "Vegetarian", "Vegan", "Keto", "Paleo", "Gluten-Free", 
                 "Dairy-Free", "Low-Sodium", "Low-Sugar", "Halal", "Kosher", "Organic Only"],
                default=st.session_state.user_profile['dietary_preferences']
            )
            
            pregnancy_status = st.selectbox(
                "Pregnancy/Nursing Status",
                ["Not Applicable", "Pregnant", "Breastfeeding", "Trying to Conceive"],
                index=0 if not st.session_state.user_profile['pregnancy_status'] else 
                ["Not Applicable", "Pregnant", "Breastfeeding", "Trying to Conceive"].index(st.session_state.user_profile['pregnancy_status'])
            )

        st.subheader("⚕️ Health Information")
        col3, col4 = st.columns(2)
        
        with col3:
            allergies = st.text_area(
                "Known Allergies & Intolerances",
                value=st.session_state.user_profile['allergies'],
                placeholder="e.g., Peanuts, Shellfish, Lactose, Gluten...",
                help="List any food allergies or intolerances (comma-separated)"
            )
            
            health_conditions = st.multiselect(
                "Health Conditions",
                ["None", "Diabetes (Type 1)", "Diabetes (Type 2)", "Hypertension", 
                 "Heart Disease", "High Cholesterol", "Kidney Disease", "Liver Disease", 
                 "Thyroid Issues", "Arthritis", "Osteoporosis", "IBS/IBD", "GERD", "Other"],
                default=st.session_state.user_profile['health_conditions']
            )
        
        with col4:
            medications = st.text_area(
                "Current Medications/Supplements",
                value=st.session_state.user_profile['medications'],
                placeholder="e.g., Blood pressure medication, Vitamin D, Multivitamin...",
                help="Include prescription medications and regular supplements"
            )

        st.markdown("---")
        st.markdown("**Required fields marked with ***")
        
        col_save, col_cancel = st.columns([1, 1])
        
        with col_save:
            save_profile = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)
        
        with col_cancel:
            cancel_setup = st.form_submit_button("❌ Cancel", use_container_width=True)

        if save_profile:
            # Validate required fields
            if not age_range or not gender or not activity_level:
                st.error("Please fill in all required fields (marked with *)")
            else:
                # Save profile to session state
                st.session_state.user_profile.update({
                    'age_range': age_range,
                    'gender': gender,
                    'weight_kg': str(weight_kg) if weight_kg > 0 else '',
                    'height_cm': str(height_cm) if height_cm > 0 else '',
                    'activity_level': activity_level,
                    'health_goals': health_goals,
                    'dietary_preferences': dietary_preferences,
                    'allergies': allergies,
                    'health_conditions': health_conditions,
                    'medications': medications,
                    'pregnancy_status': pregnancy_status,
                    'profile_complete': True
                })
                
                st.success("✅ Profile saved successfully!")
                st.info("You can now go back to the main page to get personalized analysis!")
                time.sleep(2)
                st.session_state.current_page = "main"
                st.rerun()

        if cancel_setup:
            st.session_state.current_page = "main"
            st.rerun()


def get_personalized_query_context():
    """Generate personalized context for the agent based on user profile"""
    if not st.session_state.user_profile['profile_complete']:
        return ""
    
    profile = st.session_state.user_profile
    context = f"""
    
    USER PROFILE FOR PERSONALIZED ANALYSIS:
    - Age Range: {profile['age_range']}
    - Gender: {profile['gender']}
    - Activity Level: {profile['activity_level']}
    - Health Goals: {', '.join(profile['health_goals']) if profile['health_goals'] else 'None specified'}
    - Dietary Preferences: {', '.join(profile['dietary_preferences']) if profile['dietary_preferences'] else 'None'}
    - Allergies/Intolerances: {profile['allergies'] if profile['allergies'] else 'None reported'}
    - Health Conditions: {', '.join(profile['health_conditions']) if profile['health_conditions'] else 'None reported'}
    - Medications/Supplements: {profile['medications'] if profile['medications'] else 'None reported'}
    - Pregnancy Status: {profile['pregnancy_status']}
    """
    
    if profile['weight_kg'] and profile['height_cm']:
        weight = float(profile['weight_kg'])
        height = float(profile['height_cm']) / 100  
        bmi = round(weight / (height ** 2), 1)
        context += f"\n    - BMI: {bmi}"
    
    context += """
    
    IMPORTANT: Use this profile information to provide PERSONALIZED recommendations and analysis. 
    Consider the user's specific health goals, conditions, allergies, and restrictions when analyzing the product.
    Highlight any ingredients that may be particularly beneficial or concerning for this specific user.
    """
    
    return context


def main():
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "main"
    
    initialize_user_profile()
    
    # Handle page navigation
    if st.session_state.current_page == "profile":
        profile_setup_page()
        return

    # Main page content
    st.title("ShalayeAI")
    st.html(
         """
        <div style="text-align: center;">
            <h2 style="color: #263e73; font-size: 2.2em; font-weight: 700; margin-bottom: 0.5em;">
                Your AI Sidekick for Healthier Choices 🍎🧴💊
            </h2>
            <p style="color: #555; font-size: 1.1em; line-height: 1.7; margin-bottom: 2em;">
                ShalayeAI is a wellness tool designed to empower you with knowledge about the products you consume.  
                Simply upload an image of the product label or ingredients list, and ShalayeAI will provide you with a detailed, 
                easy-to-understand breakdown of the components.  It analyzes food, drugs, and drinks, giving you the information 
                you need to make informed choices for a healthier lifestyle.
            </p>
        </div>
        """
    )

    # Initialize session state variables for the two-stage flow
    if 'initial_analysis_done' not in st.session_state:
        st.session_state.initial_analysis_done = False
    if 'full_report_content' not in st.session_state:
        st.session_state.full_report_content = None
    if 'image_path' not in st.session_state:
        st.session_state.image_path = None
    if 'chat_history' not in st.session_state: 
        st.session_state.chat_history = []
    if 'user_query' not in st.session_state:
        st.session_state.user_query = ""

    with st.sidebar:
        st.header("📤 Upload Product Image")
        
        # Profile Setup Button
        st.markdown("---")
        profile_status = "✅ Profile Complete" if st.session_state.user_profile['profile_complete'] else "⚪ No Profile"
        if st.button(f"🧑‍⚕️ Personal Profile Setup\n{profile_status}", use_container_width=True, type="secondary"):
            st.session_state.current_page = "profile"
            st.rerun()
        
        if st.session_state.user_profile['profile_complete']:
            st.success("🎯 Personalized analysis enabled!")
        else:
            st.info("💡 Set up your profile for personalized insights!")
        
        st.markdown("---")
        
        uploaded_file = st.file_uploader("Upload an image of the product or ingredients:",
                                         type=["png", "jpg", "jpeg"])
        captured_image = st.camera_input("Or take a picture of the product:")

        image_to_process = None
        if uploaded_file:
            image_to_process = uploaded_file
        elif captured_image:
            image_to_process = captured_image

        if image_to_process:
            st.image(image_to_process, caption="Image Ready for Analysis")
           
            initial_analyze_button = st.button("⚡️ Perform Analysis", use_container_width=True, type="primary")
        else:
            initial_analyze_button = False 

    # Initial Analysis Logic 
    if initial_analyze_button:
        if not image_to_process:
            st.error("Please upload an image or take a picture to perform the initial analysis.")
            return

        with st.status("🔍 ShalayeAI is analyzing your product...", expanded=True) as status:
            try:
                # Step 1: Image Processing
                status.write("1. Optimizing and preparing image for analysis...")
                time.sleep(1)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    image = optimize_image(Image.open(image_to_process))
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')
                    image.save(tmp_file.name, format='JPEG')
                    st.session_state.image_path = tmp_file.name
                status.write("✅ Image prepared successfully.")

                # Step 2: Agent Initialization
                status.write("2. Initializing ShalayeAI Agent (loading models and tools)...")
                time.sleep(0.7)
                shalaye_agent = create_shalaye_agent()
                status.write("✅ Agent initialized.")

                # Step 3: Running Agent with LLM Call
                if st.session_state.user_profile['profile_complete']:
                    status.write("3. Generating personalized analysis based on your profile...")
                else:
                    status.write("3. Sending product for comprehensive analysis...")
                
                time.sleep(1)
                
                # Build query with personalization if profile exists
                base_query = "Perform a comprehensive analysis of this product label. Provide a full report that is well expressed, explanatory, insightful and can help make informed decisions."
                personalized_context = get_personalized_query_context()
                full_query = base_query + personalized_context
                
                response = shalaye_agent.run(full_query, images=[{"filepath": st.session_state.image_path}])
                status.write("✅ ShalayeAI response received.")

                # Step 4: Processing Response
                status.write("4. Extracting structured insights and preparing the full report...")
                time.sleep(1.5)
                st.session_state.full_report_content = response.content
                st.session_state.initial_analysis_done = True
                st.session_state.chat_history = []
                status.write("✅ Report generated and ready to display.")

                status.update(label="Initial analysis successful! 🎉", state="complete", expanded=False)

            except Exception as e:
                st.error(f"❌ Error during initial analysis: Ensure you are connected to the internet and API keys are valid. Error details: {str(e)}")

    # Main Content Display Area 
    if st.session_state.initial_analysis_done and st.session_state.full_report_content:
        content = st.session_state.full_report_content

        # Show personalization status
        if st.session_state.user_profile['profile_complete']:
            st.info("🎯 This analysis is personalized based on your health profile!")

        #Display Product Identification
        detected = re.search(r'📸 Detected: (.+)', content)
        if detected:
            st.markdown(f"""
            ### Product: <span style="color: #6c5ce7;">{detected.group(1)}</span>
            ---
            """, unsafe_allow_html=True)

        # Display Parameter Breakdown 
        breakdown_text = re.search(r'🔍 Breakdown:(.+?)(?:🚨|$)', content, re.DOTALL)
        if breakdown_text:
            st.subheader("📊 Health Indicators")
            scores = extract_scores(breakdown_text.group(1))
            if scores:
                for param, score in scores.items():
                    st.markdown(f"""
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span style="color: white;">{param}</span>
                            <span style="color: #a29bfe;">{score}/5</span>
                        </div>
                        <div style="height: 8px; border-radius: 4px; background: linear-gradient(90deg, #6c5ce7, #a29bfe); width: {score*20}%;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                fig = plot_parameter_scores(scores)
                st.pyplot(fig)
            else:
                st.info("No detailed parameter scores found in the initial analysis.")

        # Display Risk Assessment
        st.subheader("⚠️ Safety Assessment")
        high_risks = extract_risks(content, "🚨 High-Risk:")
        moderate_risks = extract_risks(content, "⚠️ Moderate Risk:")
        low_risks = extract_risks(content, "✅ Low Risk:")

        if high_risks:
            st.error(f"**🚨 High-Risk Ingredients:** {', '.join(high_risks)}")
        if moderate_risks:
            st.warning(f"**⚠️ Moderate Risk Ingredients:** {', '.join(moderate_risks)}")
        if low_risks:
            st.success(f"**✅ Low Risk Ingredients:** {', '.join(low_risks)}")

        if not (high_risks or moderate_risks or low_risks):
            st.info("No specific risk categories found in the initial analysis, or all ingredients are low risk.")

        st.markdown("---")
        st.header("📝 Full Analysis Report")
        st.markdown(content, unsafe_allow_html=True)

        st.markdown("---") 
        st.header("Ask ShalayeAI More Questions!")

        # Display chat history
        for entry in st.session_state.chat_history:
            st.markdown(f"**You:** {entry['query']}")
            st.markdown(f"**ShalayeAI:** {entry['response']}")
            st.markdown("---")

        # User input for subsequent queries
        st.session_state.user_query = st.text_area("Enter your question:", key="query_input", value=st.session_state.user_query)

        # Suggested queries
        st.subheader("Suggested Follow-up Questions")
        query_buttons_follow_up = [
            "Tell me more about the benefits of [Specific Ingredient from report].",
            "Are there any alternative products with similar benefits but fewer risks?",
            "Explain the long-term effects of consuming this product.",
            "Is this safe for pregnant women?",
            "I want more information about allergies.",
        ]
        
        # Add personalized suggestions if profile exists
        if st.session_state.user_profile['profile_complete']:
            personalized_suggestions = [
                "How does this product align with my health goals?",
                "Any specific concerns based on my health conditions?",
                "Does this product interact with my medications?",
            ]
            query_buttons_follow_up = personalized_suggestions + query_buttons_follow_up

        cols_follow_up = st.columns(min(len(query_buttons_follow_up), 3))
        for i, suggestion in enumerate(query_buttons_follow_up[:6]):  # Show max 6 suggestions
            with cols_follow_up[i % 3]:
                if st.button(suggestion, key=f"suggestion_btn_{i}"):
                    st.session_state.user_query = suggestion

        submit_query_button = st.button("💬 Submit", type="secondary")

        if submit_query_button and st.session_state.user_query:
           with st.spinner(f"🤔 ShalayeAI is researching: '{st.session_state.user_query}'..."):
                try:
                    followup_agent = create_followup_agent()

                    
                    # Add personalization context to follow-up queries too
                    personalized_context = get_personalized_query_context()
                    full_follow_up_query = st.session_state.user_query + personalized_context

                    follow_up_response = followup_agent.run(
                        full_follow_up_query,
                        images=[{"filepath": st.session_state.image_path}] if st.session_state.image_path else []
                    )
                    st.session_state.chat_history.append({
                        "query": st.session_state.user_query,
                        "response": follow_up_response.content
                    })
                    st.session_state.user_query = "" 
                    st.rerun() 

                except Exception as e:
                    st.error(f"❌ Error during follow-up analysis: {str(e)}")

    # Initial State (No analysis yet)
    elif not st.session_state.initial_analysis_done and not image_to_process:
        st.info("Upload an image in the sidebar and click 'Perform Analysis' to begin.")
    elif not st.session_state.initial_analysis_done and image_to_process and not initial_analyze_button:
        st.info("Image uploaded! Click '⚡️ Perform Analysis' in the sidebar to get the core details.")

    st.markdown("---")
    st.markdown("Built with ❤️ | [Keep in touch!](https://x.com/Aethrx0)")


if __name__ == "__main__":
    main()