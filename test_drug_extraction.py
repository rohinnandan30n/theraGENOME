import requests
import json

test_queries = [
    "Is warfarin safe?",
    "What are the side effects of amoxicillin?",
    "Is aspirin good for me?",
    "Check if metformin is safe",
    "Tell me about the toxicity of ibuprofen",
]

for query_text in test_queries:
    payload = {
        "input": query_text,
        "mode": "patient",
        "context": {
            "user_input": query_text,
            "patient_allergies": [],
            "user_role": "patient"
        }
    }

    response = requests.post("http://localhost:8000/api/v1/chatbot/query", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Query: {query_text}")
        print(f"Intent: {data['intent']}")
        print(f"Drug Name: {data['variables'].get('drug_name', 'N/A')}")
        print(f"Risk Level: {data['variables'].get('risk_level', 'N/A')}")
        print()
    else:
        print(f"Error for '{query_text}': {response.status_code}")
        print(response.text)
        print()
