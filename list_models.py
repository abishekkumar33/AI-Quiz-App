from google import genai

API_KEY = "YOUR_API_KEY"   # Put the same API key from your .env here

client = genai.Client(api_key=API_KEY)

for model in client.models.list():
    print(model.name)