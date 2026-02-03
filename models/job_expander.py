from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
def expand_job_requirements(input_text):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return input_text, False
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Expand this job title into a JD: {input_text}"}],
        )
        return completion.choices[0].message.content.strip(), True
    except Exception:
        return input_text, False
