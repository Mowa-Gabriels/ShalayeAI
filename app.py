

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.exa import ExaTools
from PIL import Image
from agent_task.agent_instructions import *
from dotenv import load_dotenv
import streamlit as st
import os
import tempfile

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
                easy-to-understand breakdown of the components.  It analyze food, drugs, and drinks, giving you the information 
                you need to make informed choices for a healthier lifestyle.
            </p>

            <div style="display: flex; justify-content: center; margin-bottom: 2em;">
                
            </div>
            
        </div>
        """
    )

    # Initialize session state for image and query
    if 'query' not in st.session_state:
        st.session_state.query = "Analyze the product and provide a detailed breakdown."
    if 'image_path' not in st.session_state:  # To store image path
        st.session_state.image_path = None

    query = st.text_area("Enter your query:", key="query_input", value=st.session_state.query)

 
    analyze_button = st.button("Analyze")

    # Add some suggestive query buttons
    st.subheader("Suggested Queries")
    query_buttons = [
        "Analyze the ingredients and provide a detailed breakdown.",
        "What are the potential health effects of the ingredients?",
        "Tell me about the risks and benefits of this product.",
        "I want more information about allergies.",
    ]
    cols = st.columns(len(query_buttons))
    for i, suggestion in enumerate(query_buttons):
        with cols[i]:
            if st.button(suggestion,
                           
                           ):
                st.session_state.query = suggestion
                
    with st.sidebar:
        st.header("Upload/Take Product Image")
        # File uploader for images
        uploaded_file = st.file_uploader("Upload an image of the product or ingredients:",
                                         type=["png", "jpg", "jpeg"])

        # Camera input
        captured_image = st.camera_input("Take a picture of the product or ingredients")  # added camera input

        # Determine which image to use
        image_to_process = None
        if uploaded_file:
            image_to_process = uploaded_file
        elif captured_image:
            image_to_process = captured_image

        # Display the uploaded image
        if image_to_process:
            st.image(image_to_process, caption="Uploaded Image")

    if analyze_button:  
        if not image_to_process:
            st.error("Please upload an image or take a picture.")
            return

        with st.spinner("Analyzing Product..."):
            try:
                # Image Processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    image = optimize_image(Image.open(image_to_process))
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')
                    image.save(tmp_file.name, format='JPEG')
                    image_path = tmp_file.name  # Get the path to the temp file
                    st.session_state.image_path = image_path #store image path

                shalaye_agent = create_shalaye_agent()

                # Pass the image data and query to the agent
                response = shalaye_agent.run(query, images=[{"filepath": image_path}])
                st.write("Analysis Results:")
                st.markdown(response.content, unsafe_allow_html=True)


            except Exception as e:
                st.error(f"❌ Error during analysis: Ensure you are connected to the internet")
            finally:
                if st.session_state.image_path:
                    os.remove(st.session_state.image_path) 


    st.markdown("---")
    st.markdown("Built with ❤️ | [Keep in touch!](https://x.com/Aethrx0)")

if __name__ == "__main__":
    main()

