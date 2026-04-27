from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()

from engine import get_best_cards, optimize_redemption, compare_cards
from llm import classify_intent, explain_recommendation, explain_redemption

app = FastAPI(title="CreditSavvy AI", description="Credit Card Rewards & Points Optimization Chatbot", version="1.0.0")

class ChatRequest(BaseModel):
    message: str

class RecommendRequest(BaseModel):
    category: str
    amount: float

class RedeemRequest(BaseModel):
    points: int

class CompareRequest(BaseModel):
    card1: str
    card2: str


@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r") as f:
        return f.read()

@app.post("/chat")
def chat(request: ChatRequest):
    """
    Main orchestrator endpoint.
    1. Uses LLM to extract intent (category, amount).
    2. Runs deterministic engine.
    3. Uses LLM to explain the engine's result.
    """
    # 1. Intent Classification
    intent = classify_intent(request.message)
    intent_type = intent.get("intent_type", "spend")

    if intent_type == "redeem":
        points = intent.get("points", 0)
        if points <= 0:
            return {"error": "Could not determine the number of points to redeem."}
            
        options = optimize_redemption(points)
        explanation = explain_redemption(points, options)
        
        return {
            "intent": intent,
            "explanation": explanation
        }
    else:
        category = intent.get("category", "General")
        amount = intent.get("amount", 0.0)
        
        if amount <= 0:
            return {"error": "Could not determine a valid spend amount from your message."}
            
        top_cards, meta = get_best_cards(category, amount)
        explanation = explain_recommendation(top_cards, meta)
        
        return {
            "intent": intent,
            "recommendations": top_cards,
            "explanation": explanation
        }

@app.post("/recommend")
def recommend_cards(request: RecommendRequest):
    """
    Direct endpoint for recommendation engine (Bypasses initial LLM intent step).
    """
    top_cards, meta = get_best_cards(request.category, request.amount)
    explanation = explain_recommendation(top_cards, meta)
    return {
        "recommendations": top_cards,
        "explanation": explanation
    }

@app.post("/redeem")
def redeem_points(request: RedeemRequest):
    """
    Evaluates redemption value for points and explains the strategy.
    """
    options = optimize_redemption(request.points)
    explanation = explain_redemption(request.points, options)
    
    return {
        "total_points": request.points,
        "options": options,
        "best_strategy": explanation
    }

@app.post("/compare")
def compare(request: CompareRequest):
    """
    Compares two credit cards deterministically.
    """
    result = compare_cards(request.card1, request.card2)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

if __name__ == "__main__":
    import uvicorn
    # Make sure this runs properly locally if called directly
    uvicorn.run(app, host="0.0.0.0", port=8000)
