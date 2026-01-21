import os
import vertexai
from vertexai.generative_models import GenerativeModel
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# --- 1. CONFIGURATION ---
PROJECT_ID = "your-project-id"  # <--- REPLACE THIS
LOCATION = "us-central1"

# Initialize Vertex AI SDK
vertexai.init(project=PROJECT_ID, location=LOCATION)

app = FastAPI(title="Sequential Code Generator Agent")

# --- 2. DATA MODELS ---
class CodeRequest(BaseModel):
    requirement: str
    language: str = "Python"

class WorkflowResponse(BaseModel):
    initial_draft: str
    review_comments: str
    final_code: str

# --- 3. AGENT DEFINITIONS ---
# We use standard GenerativeModel for granular control over system prompts.

# AGENT A: The Drafter
# Role: Write the initial code based on the user's prompt.
draft_agent = GenerativeModel(
    "gemini-1.5-flash",
    system_instruction="""You are an expert software engineer. 
    Write clean, functional code based on the user's requirements. 
    Output ONLY the code, no markdown formatting or explanation."""
)

# AGENT B: The Reviewer
# Role: Find bugs, security issues, or style errors in the draft.
reviewer_agent = GenerativeModel(
    "gemini-1.5-flash",
    system_instruction="""You are a Senior Staff Engineer and Code Reviewer.
    Analyze the provided code for bugs, inefficiencies, and security risks.
    Provide a concise list of required changes. If the code is perfect, say "No changes needed"."""
)

# AGENT C: The Final Writer
# Role: Rewrite the code incorporating the reviewer's feedback.
final_writer_agent = GenerativeModel(
    "gemini-1.5-flash",
    system_instruction="""You are a Tech Lead. 
    You will receive an initial code draft and a set of review comments.
    Rewrite the code to fix all issues mentioned in the review.
    Output ONLY the final corrected code, no markdown."""
)

# --- 4. THE SEQUENTIAL ORCHESTRATOR ---
@app.post("/generate-code", response_model=WorkflowResponse)
async def sequential_workflow(payload: CodeRequest):
    try:
        # STEP 1: Draft Code
        print(f"--- [1/3] Drafting {payload.language} code... ---")
        draft_prompt = f"Write {payload.language} code for: {payload.requirement}"
        draft_response = await draft_agent.generate_content_async(draft_prompt)
        draft_code = draft_response.text

        # STEP 2: Code Review
        print(f"--- [2/3] Reviewing code... ---")
        review_prompt = f"""
        Review this code:
        {draft_code}
        """
        review_response = await reviewer_agent.generate_content_async(review_prompt)
        review_comments = review_response.text

        # STEP 3: Final Polish
        print(f"--- [3/3] Finalizing code... ---")
        final_prompt = f"""
        Original Code:
        {draft_code}

        Reviewer Comments:
        {review_comments}

        Task: Rewrite the original code to address the comments.
        """
        final_response = await final_writer_agent.generate_content_async(final_prompt)
        final_code = final_response.text

        # Return the full artifact history for transparency
        return {
            "initial_draft": draft_code,
            "review_comments": review_comments,
            "final_code": final_code
        }

    except Exception as e:
        # Log the error for debugging
        print(f"Error in workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 5. RUNNER ---
if __name__ == "__main__":
    import uvicorn
    # Run with: python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
