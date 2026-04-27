from llm import explain_recommendation
import sys

try:
    print(explain_recommendation([{"card": "test_card"}], {"category": "test", "amount": 100}))
except Exception as e:
    print("Caught:", e)
