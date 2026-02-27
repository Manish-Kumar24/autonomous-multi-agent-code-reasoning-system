import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
def ask_llama(messages, temperature=0.2, model="llama-3.3-70b-versatile"):
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=2000
    )
    return completion.choices[0].message.content