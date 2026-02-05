import sys
import os
print("Importing google.generativeai...")
import google.generativeai as genai
print("google.generativeai imported.")

sys.path.append(os.getcwd())
print("Importing app.config...")
from app.config import settings
print("app.config imported.")

print("Importing app.llm.gemini...")
from app.llm.gemini import GeminiClient
print("app.llm.gemini imported.")
