import re
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_dataset(filepath: str) -> dict:
    """Loads the dataset from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading dataset from {filepath}: {e}")
        return {"cards": []}

def extract_cashback_percentage(rate_notes: str) -> float:
    """
    Attempts to extract the maximum cashback percentage mentioned in a text string.
    E.g. '5% on online spends' -> 5.0
    Fallback for deterministic logic when 'value_per_point_rupees' is 0.
    """
    if not rate_notes:
        return 0.0
    
    # Look for digits followed by %
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", rate_notes)
    if matches:
        return max(float(m) for m in matches)
    return 0.0

def normalize_category(user_category: str) -> str:
    """
    Given an input string that the LLM provides, normalize it to standard categories
    if it matches them somewhat cleanly. (Alternatively, the LLM will just return the standardized).
    """
    user_category = user_category.lower()
    mapping = {
        "dining": "Dining",
        "food": "Dining",
        "travel": "Travel",
        "flight": "Travel",
        "hotel": "Travel",
        "grocery": "Groceries",
        "groceries": "Groceries",
        "utility": "Utility",
        "bills": "Utility",
        "fuel": "Fuel",
        "gas": "Fuel",
        "online": "Online Shopping",
        "shopping": "Online Shopping",
    }
    for key, val in mapping.items():
        if key in user_category:
            return val
    return "General"
