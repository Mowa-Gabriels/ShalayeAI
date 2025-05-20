# shalaye_utils.py
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