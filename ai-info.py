from constants import GEMINI_MODEL
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

prompt = "Find the race condition in this multi-threaded C++ snippet: [code here]"

response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents=prompt,
)

print(response.text)