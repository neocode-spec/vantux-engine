import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(title="Vantux Sovereign Engine Core")

# Securely grab the API key from your computer/server environment
# This keeps it completely invisible to your frontend users
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# Define what data the client needs to send us
class SimulationRequest(BaseModel):
    scenario: str
    model_name: str = "gemini-3.5-flash"

@app.post("/simulate")
async def run_simulation(request: SimulationRequest):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Vantux Server Error: Master Key not configured.")
    
    try:
        # The secret sauce: The server uses YOUR key to talk to Google
        model = genai.GenerativeModel(
            model_name=request.model_name,
            system_instruction="You are the Sovereign What-If Simulation Engine. Your goal is human resilience and technical survival."
        )
        response = model.generate_content(request.scenario)
        
        # Send ONLY the final answer back to the user
        return {"result": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
