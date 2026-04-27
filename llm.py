import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Ensure GEMINI_API_KEY is available
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
else:
    # Use default environment credential discovery
    client = genai.Client()

# Define schema for intent extraction
class ChatIntent(BaseModel):
    intent_type: str = Field(description="Must be 'spend' for buying something, or 'redeem' for using reward points.")
    category: str = Field(description="The spend category (e.g., Dining, Travel). Return 'General' if redeeming points.")
    amount: float = Field(description="The numeric amount being spent. Return 0.0 if redeeming points.")
    points: int = Field(description="The numeric amount of reward points the user wants to redeem. Return 0 if spending.")

def classify_intent(user_input: str) -> dict:
    """
    Uses Gemini to classify intent and extract category/amount via structured outputs.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Extract the intent, category, amount, and points from this text: '{user_input}'",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ChatIntent,
                temperature=0.1
            ),
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"Error calling LLM for intent: {e}")
        return {"intent_type": "spend", "category": "General", "amount": 0.0, "points": 0}

def explain_recommendation(top_cards: list, meta: dict) -> str:
    """
    Generates a human-readable explanation of why these cards were chosen.
    """
    prompt = f"""
You are a top-tier Indian credit card financial advisor.
The user wants to spend Rs. {meta['amount']} on {meta['category']}.
The deterministic engine has calculated these top 3 cards based on hard math:

{json.dumps(top_cards, indent=2)}

Write a professional, easy-to-understand explanation for why the top card is recommended, 
and briefly summarize the 2nd and 3rd options. Be concise and use bullet points where helpful.
Do not invent or change the math values provided to you; just explain them naturally.
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3
            ),
        )
        return response.text
    except Exception as e:
        print(f"Error generating explanation: {e}")
        return "Explanation could not be generated at this time."

def explain_redemption(points: int, options: list) -> str:
    """
    Generates an explanation for the best redemption strategies.
    """
    prompt = f"""
The user has {points} reward points.
The deterministic ranker has evaluated the redemption options as follows:

{json.dumps(options, indent=2)}

Act as a financial advisor explaining how the user should optimally use their points.
Highlight the best value (highest Rs value) and mention trade-offs if they chose the lowest value option (like Merchandise).
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3
            ),
        )
        return response.text
    except Exception as e:
        print(f"Error generating redemption explanation: {e}")
        return "Redemption explanation could not be generated at this time."
