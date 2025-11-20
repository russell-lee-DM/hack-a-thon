import google.generativeai as genai

# Your actual Key
GOOGLE_API_KEY = "AIzaSyB5w-G1X6AjfzBmD337RbhRqSZBeE2HETo"
genai.configure(api_key=GOOGLE_API_KEY)

print("--- CHECKING AVAILABLE MODELS ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"VALID MODEL FOUND: {m.name}")
except Exception as e:
    print(f"Error: {e}")