"""List the Gemini models your key can use for generateContent.

Run:  python list_models.py
The key is read from .env - never hard-code it in this file.
"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if not api_key:
    raise SystemExit("GEMINI_API_KEY is missing. Create .env from .env.example first.")

client = genai.Client(api_key=api_key)
for model in client.models.list():
    actions = getattr(model, "supported_actions", None) or []
    if "generateContent" in actions:
        print(model.name)