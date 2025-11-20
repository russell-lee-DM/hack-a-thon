# main.py - The Hackathon Backend
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import shutil

app = FastAPI()

# --- 1. YOUR CONFIGURATION ---
# We are hardcoding the key here for the Hackathon speed.
# In production, you would use os.getenv()
GOOGLE_API_KEY = "AIzaSyB5w-G1X6AjfzBmD337RbhRqSZBeE2HETo" 
genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. CORS MIDDLEWARE (Crucial for connecting to Builder.io) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- 3. THE "SMART" SOP CHECKLIST ---
# This is the "Brain" that tells Gemini what to look for.
# It includes the trap for the Westbound PDF (The missing $42.5k fee).
SOP_CHECKLIST = """
You are a strict Compliance Officer for DealMaker Securities. 
Review the attached 'Form C' PDF against the following MANDATORY RULES.

1. INTERMEDIARY FEES (CRITICAL CHECK)
   - Intermediary Name must be "DealMaker Securities LLC".
   - CRD Number must be exactly "315324".
   - Commission must be "8.5%".
   - **SETUP FEE CHECK:** The document MUST explicitly disclose a "$42,500" advance setup fee. 
     (NOTE: If the document lists a monthly fee (e.g. $15,000) but fails to list the $42,500 setup fee, MARK THIS AS A HIGH SEVERITY FAILURE).

2. ISSUER ELIGIBILITY
   - Issuer Name: Westbound & Down Brewing, Inc.
   - Organized: Delaware.
   - Target Offering Amount: Must be greater than $10,000.

3. FINANCIAL HEALTH CHECK
   - Scan the 'Financial Information' table.
   - If the 'Net Income' for the most recent fiscal year is negative (loss), FLAG this as a Risk Factor.
   - Compare 'Cash' on hand vs 'Current Liabilities'. If Cash is lower than liabilities, FLAG as Liquidity Risk.

4. SIGNATURES
   - Verify "Jacob Gardner" has signed as Principal Executive Officer.
"""

@app.post("/scan")
async def scan_pdf(file: UploadFile = File(...)):
    # Create a temporary filename
    temp_filename = f"temp_{file.filename}"
    
    try:
        # 1. Save the file locally so we can send it to Google
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Upload the file to Gemini
        print(f"Uploading {file.filename} to Gemini...")
        uploaded_file = genai.upload_file(path=temp_filename, display_name=file.filename)
        print(f"Upload complete: {uploaded_file.uri}")
        
        # 3. Initialize the Model
        # gemini-1.5-flash is fast and free for this tier
        # model = genai.GenerativeModel('gemini-1.5-flash')
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 4. The Prompt
        prompt = f"""
        {SOP_CHECKLIST}

        INSTRUCTIONS:
        Analyze the uploaded PDF. Cross-reference it with the rules above.
        Return a JSON object ONLY. Do not use markdown formatting (no ```json blocks).
        
        Use this exact JSON structure:
        {{
            "compliance_score": (integer 0-100),
            "summary": "Brief summary of findings...",
            "issues": [
                {{
                    "severity": "High" | "Medium" | "Low",
                    "rule": "Name of the rule violated",
                    "description": "Exact details of the error found."
                }}
            ]
        }}
        """
        
        # 5. Run the Analysis
        print("Analyzing document...")
        response = model.generate_content([prompt, uploaded_file])
        
        # 6. Return the text (which is valid JSON)
        return {
            "status": "success",
            "filename": file.filename,
            "ai_analysis": response.text
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}
    
    finally:
        # Cleanup: Remove the local temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

# This runs the server when you type `python main.py`
if __name__ == "__main__":
    import uvicorn
    print("Starting Server on Port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)