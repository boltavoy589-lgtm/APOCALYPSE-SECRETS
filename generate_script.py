import os, json, requests

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPT = """You write scripts for MINDSPARK, a YouTube Shorts channel about psychology, mind facts, science and AI.
Write ONE short script (35-45 seconds, 90-110 words) in English.
Rules:
- Start with a strong hook in the first sentence.
- Use one true, well-known fact. Never invent studies or numbers.
- Simple words, short sentences.
- End with a short question to the viewer.
Return ONLY JSON with keys:
"topic", "script", "title" (max 60 chars),
"description" (2-3 sentences plus 3 hashtags including #Shorts),
"tags" (list of 8 short strings),
"visual_keywords" (list of 6 single English words for stock footage).
"""

def main():
    r = requests.post(
        URL,
        headers={"x-goog-api-key": API_KEY, "Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": PROMPT}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0},
        },
        timeout=120,
    )
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    data = json.loads(text)
    with open("script.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
