import os
from typing import List, Dict, Any
from utils import load_json_dataset, extract_cashback_percentage, normalize_category

DATASET_PATH = os.path.join(os.path.dirname(__file__), "Credit Card Database.txt")
db = load_json_dataset(DATASET_PATH)
cards_data = db.get("cards", [])

def get_best_cards(category: str, amount: float) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Ranks cards deterministically based on spend category and amount.
    Returns the top 3 cards and their full reward breakdown.
    """
    norm_cat = normalize_category(category)
    results = []

    for card in cards_data:
        breakdown = card.get("rewards_breakdown", {})
        base_pts = breakdown.get("base_reward_points", 0)
        pts_per_spend = breakdown.get("points_per_spend", 0)
        val_per_pt = breakdown.get("value_per_point_rupees", 0.0)
        
        # Determine if category is a match for accelerated rewards
        is_best_for = any(norm_cat.lower() in b.lower() for b in card.get("best_for", []))
        
        calculated_value = 0.0
        logic_explanation = ""

        # Deterministic logic using dataset structured parts:
        if base_pts > 0 and pts_per_spend > 0 and val_per_pt > 0:
            base_reward_value = (amount / pts_per_spend) * base_pts * val_per_pt
            
            if is_best_for:
                # Apply an accelerated multiplier if it's their best category
                # E.g., HDFC says up to 10X on smartbuy, Axis says 5X, etc.
                # Here we deterministically assign a 3x multiplier to simulate "Best For"
                calculated_value = base_reward_value * 3
                logic_explanation = f"Base points: {base_pts} per {pts_per_spend}. Accelerated (x3) for {norm_cat} match."
            else:
                calculated_value = base_reward_value
                logic_explanation = f"Base points: {base_pts} per {pts_per_spend}. Flat base rate applied."
                
        else:
            # Fallback to text parsing (cashback % cards)
            cashback_str = card.get("cashback_rate", "")
            percentage = extract_cashback_percentage(cashback_str)
            
            if is_best_for:
                # Use max extracted %
                calculated_value = amount * (percentage / 100)
                logic_explanation = f"Extracted {percentage}% max cashback rate because it matches {norm_cat}."
            else:
                # Base 1% fallback
                calculated_value = amount * 0.01
                logic_explanation = "Base 1% fallback applied as category was not a primary match."

        result_item = {
            "card_name": card["card_name"],
            "bank": card["bank"],
            "reward_value": round(calculated_value, 2),
            "logic_applied": logic_explanation,
            "best_for": card["best_for"],
            "annual_fee": card["annual_fee"]
        }
        results.append(result_item)

    # Rank by highest reward value
    results.sort(key=lambda x: x["reward_value"], reverse=True)
    top_3 = results[:3]

    return top_3, {"category": norm_cat, "amount": amount, "total_cards_evaluated": len(cards_data)}

def optimize_redemption(points: int) -> List[Dict[str, Any]]:
    """
    Computes deterministic value of points across different categories.
    """
    # Deterministic fixed value ratios (often true for average points system)
    ratios = {
        "Travel (Flights/Hotels)": 1.0,
        "Cashback / Statement Credit": 0.5,
        "Partner Conversions (Miles)": 0.4,
        "Gift Cards (Amazon/Flipkart)": 0.35,
        "Merchandise Catalog": 0.25
    }
    
    options = []
    for option_name, conversion_rate in ratios.items():
        value = points * conversion_rate
        options.append({
            "redemption_type": option_name,
            "value_rupees": round(value, 2),
            "conversion_rate": conversion_rate
        })
    
    # Sort highest value first
    options.sort(key=lambda x: x["value_rupees"], reverse=True)
    return options

def compare_cards(card1_name: str, card2_name: str) -> Dict[str, Any]:
    """
    Compares two cards based on dataset features.
    """
    c1 = next((c for c in cards_data if c["card_name"].lower() == card1_name.lower()), None)
    c2 = next((c for c in cards_data if c["card_name"].lower() == card2_name.lower()), None)

    if not c1 or not c2:
        return {"error": "One or both cards not found in dataset."}

    return {
        "comparison": {
            "card1": {"name": c1["card_name"], "annual_fee": c1["annual_fee"], "best_for": c1["best_for"]},
            "card2": {"name": c2["card_name"], "annual_fee": c2["annual_fee"], "best_for": c2["best_for"]},
        }
    }
