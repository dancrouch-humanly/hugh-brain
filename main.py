import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# We get the API key from the environment settings later
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# *** PASTE YOUR HUBSPOT LINK INSIDE THE QUOTES BELOW ***
CALENDAR_LINK = "https://meetings.hubspot.com/dan-crouch"

SYSTEM_PROMPT = """
You are Hugh, Humanly's AI SDR. 
You are efficient, conversational, and patient.

RULES:
1. If the user gives you a URL, pretend to read it instantly and say: 
   "I see you are hiring for [Role]. That looks like a high volume role. Shall I interview you?"
   (Invent a plausible role like Sales Rep or Engineer if the scrape fails).

2. If the user agrees to a meeting or seems qualified, say EXACTLY this phrase:
   "[ACTION:CALENDAR] Great, I'm opening my calendar now."
   Do not say anything else after that tag.
"""

@app.get("/")
def home():
    return {"status": "Hugh is alive and listening"}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()

    # Tavus sends the user's spoken text in a field called 'text' (or sometimes 'query')
    user_message = data.get("text", "")
    if not user_message:
        user_message = data.get("query", "Hello")

    # --- THE MAGIC TRICK (Simple Web Scraper) ---
    if "http" in user_message:
        try:
            # Extract the URL (very basic way)
            url = [word for word in user_message.split() if word.startswith("http")][0]
            # Try to grab the title of the page
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            page_title = soup.title.string if soup.title else "your website"

            # We inject this knowledge into the chat context
            user_message += f" (SYSTEM NOTE: I checked the URL {url}. The page title is '{page_title}'. Use this to sound smart.)"
        except:
            # If scraping fails, we just ignore it and let the AI improvise
            pass

    # --- SEND TO OPENAI ---
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    ai_response = completion.choices[0].message.content

    # Return the response to Tavus
    return JSONResponse(content={"speech": ai_response})

# This line runs the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
