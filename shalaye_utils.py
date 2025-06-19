import streamlit as st
import re
from PIL import Image
import matplotlib.pyplot as plt

def optimize_image(image: Image.Image) -> Image.Image:
    """
    Optimizes an image for analysis by resizing and converting it to JPEG.

    Args:
        image: A PIL Image object.

    Returns:
        An optimized PIL Image object.
    """
    max_size = (720, 720)
    image.thumbnail(max_size, Image.LANCZOS) # Use LANCZOS for high-quality downsampling
    return image

def extract_scores(breakdown_text: str) -> dict:
    """
    Extracts parameter scores from the agent's breakdown text.

    Args:
        breakdown_text: The string containing the ingredient breakdown.

    Returns:
        A dictionary with parameter names as keys and scores (0-5) as integer values.
    """
    params = {}
    # Matches lines like "- Parameter Name: Score"
    matches = re.findall(r'- (.*?): (\d)', breakdown_text)
    for param, score in matches:
        params[param.strip()] = int(score)
    return params

def extract_risks(text_block: str, risk_type: str) -> list[str]:
    """
    Extracts a list of risks for a given risk type from the agent's full analysis.

    Args:
        text_block: The full analysis text from the agent.
        risk_type: The specific risk type to extract (e.g., "🚨 High-Risk:").

    Returns:
        A list of cleaned risk strings.
    """
    # Matches lines like "🚨 High-Risk: item1, item2"
    pattern = rf"{re.escape(risk_type)}\s*(.*)" # re.escape to handle special regex characters in risk_type
    match = re.search(pattern, text_block)
    if match:
        # Split by comma and strip whitespace from each item
        risks = [risk.strip() for risk in match.group(1).split(',')]
        # Filter out any empty strings that might result from extra commas or malformed lists
        return [risk for risk in risks if risk]
    return []

def plot_parameter_scores(scores: dict):
    """
    Generates a matplotlib bar plot of parameter scores.

    Args:
        scores: A dictionary with parameter names and their scores.

    Returns:
        A matplotlib Figure object.
    """
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8,4), facecolor='#1e1e1e')
    colors = ['#6c5ce7', '#a29bfe', '#74b9ff', '#55efc4', '#ffeaa7'] # Example colors
    
    # Ensure consistent order if needed, otherwise Python 3.7+ dicts preserve insertion order
    # For plotting, it's often good to sort for consistency
    sorted_params = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    param_names = [item[0] for item in sorted_params]
    param_values = [item[1] for item in sorted_params]

    bars = ax.barh(param_names, param_values, color=colors[:len(param_names)]) # Use enough colors
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{width}', va='center', ha='left', color='white')
    
    ax.set_xlim(0,5.5) # Extend x-limit slightly for text
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#6c5ce7')
    ax.spines['left'].set_color('#6c5ce7')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    plt.tight_layout()
    return fig


def apply_anthropic_theme():
    st.html(
        """
        <style>
        /* Import fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Root variables - Anthropic dark theme */
        :root {
            --primary-color: #D97757;
            --secondary-color: #B85D3E;
            --secondary-background: #2C2A29;
            --text-color: #F7F3F0;
            --accent-color: #E8B893;
            --border-color: #3D3A38;
            --hover-color: #413E3C;
            --success-color: #52C41A;
            --warning-color: #FAAD14;
            --error-color: #FF4D4F;
        }
        
        /* Global font smoothing */
        * {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        /* Main app background */
        .stApp {
            background-color: var(--background-color) !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Typography hierarchy */
        h1 {
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            color: var(--text-color) !important;
            margin-bottom: 1rem !important;
        }
        
        h2 {
            font-size: 2rem !important;
            font-weight: 600 !important;
            color: var(--text-color) !important;
            margin-bottom: 0.8rem !important;
        }
        
        h3 {
            font-size: 1.5rem !important;
            font-weight: 500 !important;
            color: var(--text-color) !important;
            margin-bottom: 0.6rem !important;
        }
        
        /* Sidebar styling */
        .stSidebar {
            background-color: var(--secondary-background) !important;
            border-right: 1px solid var(--border-color) !important;
        }
        
        .stSidebar .stButton > button {
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }
        
        .stSidebar .stButton > button:hover {
            background-color: var(--secondary-color) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(217, 119, 87, 0.3) !important;
        }
        
        /* Primary buttons */
        .stButton > button[data-baseweb="button"][kind="primary"] {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button[data-baseweb="button"][kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(217, 119, 87, 0.4) !important;
        }
        
        /* Secondary buttons */
        .stButton > button {
            background-color: var(--secondary-background) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            font-weight: 400 !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            background-color: var(--hover-color) !important;
            border-color: var(--primary-color) !important;
        }
        
        /* Form inputs */
        .stSelectbox > div > div {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            color: var(--text-color) !important;
        }
        
        .stTextInput > div > div > input {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            color: var(--text-color) !important;
        }
        
        .stTextArea > div > div > textarea {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            color: var(--text-color) !important;
        }
        
        /* File uploader */
        .stFileUploader > div {
            background-color: var(--secondary-background) !important;
            border: 2px dashed var(--border-color) !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        .stFileUploader > div:hover {
            border-color: var(--primary-color) !important;
            background-color: var(--hover-color) !important;
        }
        
        /* Status containers */
        .stAlert {
            border-radius: 8px !important;
            border: none !important;
        }
        
        .stAlert[data-baseweb="notification"][kind="info"] {
            background-color: rgba(24, 144, 255, 0.1) !important;
            border-left: 4px solid #1890FF !important;
        }
        
        .stAlert[data-baseweb="notification"][kind="success"] {
            background-color: rgba(82, 196, 26, 0.1) !important;
            border-left: 4px solid var(--success-color) !important;
        }
        
        .stAlert[data-baseweb="notification"][kind="warning"] {
            background-color: rgba(250, 173, 20, 0.1) !important;
            border-left: 4px solid var(--warning-color) !important;
        }
        
        .stAlert[data-baseweb="notification"][kind="error"] {
            background-color: rgba(255, 77, 79, 0.1) !important;
            border-left: 4px solid var(--error-color) !important;
        }
        
        /* Metrics */
        .stMetric {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }
        
        /* Expander */
        .stExpander {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
        }
        
        /* Form container */
        .stForm {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            padding: 1.5rem !important;
        }
        
        /* Progress bars */
        .stProgress .st-bo {
            background-color: var(--primary-color) !important;
        }
        
        /* Spinner */
        .stSpinner {
            color: var(--primary-color) !important;
        }
        
        /* Custom card styling */
        .analysis-card {
            background: linear-gradient(135deg, var(--secondary-background), var(--hover-color)) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin: 1rem 0 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
        }
        
        .analysis-card:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* Health indicator bars */
        .health-indicator {
            background: linear-gradient(90deg, var(--primary-color), var(--accent-color)) !important;
            border-radius: 4px !important;
            height: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        /* Chat styling */
        .stChatMessage {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
        }
        
        /* Multiselect */
        .stMultiSelect > div {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
        }
        
        /* Text color adjustments */
        .stMarkdown, .stText, p, div, span, label {
            color: var(--text-color) !important;
        }
        
        /* Special styling for profile status */
        .profile-complete {
            background: linear-gradient(135deg, var(--success-color), #73d13d) !important;
            color: white !important;
            padding: 0.5rem 1rem !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }
        
        .profile-incomplete {
            background: linear-gradient(135deg, var(--warning-color), #ffc53d) !important;
            color: var(--background-color) !important;
            padding: 0.5rem 1rem !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }
        
        /* Navigation styling */
        [data-testid="stSidebarNav"] {
            background-color: var(--secondary-background) !important;
        }
        
        [data-testid="stSidebarNav"] li a {
            color: var(--text-color) !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        [data-testid="stSidebarNav"] li a:hover {
            background-color: var(--hover-color) !important;
        }
        
        /* Form styling improvements */
        .stNumberInput > div > div > input {
            background-color: var(--secondary-background) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            color: var(--text-color) !important;
        }
        
        /* Custom header styling */
        .anthropic-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            font-weight: 700 !important;
            text-align: center !important;
            margin-bottom: 2rem !important;
        }
        </style>
        """
    )

