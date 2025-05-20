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

def main():
    st.title("""
             ShalayeAI
             """
    )
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
    # No initial value for query, this ine gats dey blank until user type
    if 'user_query' not in st.session_state:
        st.session_state.user_query = ""


 
    with st.sidebar:
        st.header("📤 Upload Product Image")
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
                time.sleep(1) # Simulate work so you can see the message
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    image = optimize_image(Image.open(image_to_process))
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')
                    image.save(tmp_file.name, format='JPEG')
                    st.session_state.image_path = tmp_file.name
                status.write("✅ Image prepared successfully.") # Confirmation for step 1

                # Step 2: Agent Initialization
                status.write("2. Initializing ShalayeAI Agent (loading models and tools)...")
                time.sleep(0.7) # Simulate work
                shalaye_agent = create_shalaye_agent()
                status.write("✅ Agent initialized.") # Confirmation for step 2

                # Step 3: Running Agent with LLM Call
                status.write("3. Sending product for comprehensive analysis...")
                time.sleep(1) # Simulate LLM/Tool call time
                initial_query_for_agent = "Perform a comprehensive analysis of this product label. Provide a full report that is well expressed, explanatory, insightful and csn help make informed decisions."
                response = shalaye_agent.run(initial_query_for_agent, images=[{"filepath": st.session_state.image_path}])
                status.write("✅ ShalayeAI response received.") # Confirmation for step 3

                # Step 4: Processing Response
                status.write("4. Extracting structured insights and preparing the full report...")
                time.sleep(1.5) # Simulate work
                st.session_state.full_report_content = response.content
                st.session_state.initial_analysis_done = True
                st.session_state.chat_history = []
                status.write("✅ Report generated and ready to display.") # Confirmation for step 4

                # Final Update to change the main label and state, and collapse
                status.update(label="Initial analysis successful! 🎉", state="complete", expanded=False)


            except Exception as e:
                st.error(f"❌ Error during initial analysis: Ensure you are connected to the internet and API keys are valid. Error details: {str(e)}")
            finally:
                pass 


    # Main Content Display Area 
    # We go display initial analysis results if e dey available
    if st.session_state.initial_analysis_done and st.session_state.full_report_content:
        content = st.session_state.full_report_content

        #Display Product Identification
        detected = re.search(r'📸 Detected: (.+)', content)
        if detected:
            st.markdown(f"""
            ### Product: <span style="color: #6c5ce7;">{detected.group(1)}</span>
            ---
            """, unsafe_allow_html=True)

        # Display Parameter Breakdown 
        breakdown_text = re.search(r'🔍 Breakdown:(.+?)(?:🚨|$)', content, re.DOTALL) # Use (?:🚨|$) to match till end if no 🚨
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
                # Plot the scores
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

        # Subsequent Queries
        # Display chat history
        for entry in st.session_state.chat_history:
            st.markdown(f"**You:** {entry['query']}")
            st.markdown(f"**ShalayeAI:** {entry['response']}")
            st.markdown("---")

        # User input for subsequent queries
        st.session_state.user_query = st.text_area("Enter your question:", key="query_input", value=st.session_state.user_query)

        # Suggested queries for subsequent queries
        st.subheader("Suggested Follow-up Questions")
        query_buttons_follow_up = [
            "Tell me more about the benefits of [Specific Ingredient from report].",
            "Are there any alternative products with similar benefits but fewer risks?",
            "Explain the long-term effects of consuming this product.",
            "Is this safe for pregnant women?",
            "I want more information about allergies.",
        ]
        cols_follow_up = st.columns(len(query_buttons_follow_up))
        for i, suggestion in enumerate(query_buttons_follow_up):
            with cols_follow_up[i]:
                if st.button(suggestion, key=f"suggestion_btn_{i}"):
                    st.session_state.user_query = suggestion


        submit_query_button = st.button("💬 Submit", type="secondary")

        if submit_query_button and st.session_state.user_query:
           with st.spinner(f"🤔 ShalayeAI is researching: '{st.session_state.user_query}'..."):
                try:
                    shalaye_agent = create_shalaye_agent() 

                    follow_up_response = shalaye_agent.run(
                        st.session_state.user_query,
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

    # --- Final Cleanup (ensure temp file is removed when app state resets, e.g., browser close) ---
    # For robust cleanup on fresh start/image change,  handle it in initial_analyze_button.
    # You might want a dedicated clear button to clean up if needed.

    st.markdown("---")
    st.markdown("Built with ❤️ | [Keep in touch!](https://x.com/Aethrx0)")


if __name__ == "__main__":
    main()

