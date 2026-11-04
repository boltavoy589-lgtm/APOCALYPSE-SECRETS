import os, json, re, requests

API_KEY = os.environ["GROQ_API_KEY"]
URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"

PROMPT = """
Write one YouTube Shorts script for a channel called APOCALYPSE SECRETS.
Topic: a zombie apocalypse scenario, survival psychology, or how people behave under fear.
Rules:
- Clearly fictional or speculative. Never claim a real event happened.
- Psychology facts must be real and well-known. Do not invent studies, names or numbers.
- Do not teach how to manipulate or deceive people. Explain psychology as something to recognize and resist.
- 90-110 words, simple English, strong hook in the first sentence, end with a question to the viewer.
Return ONLY a JSON object (no markdown, no extra text) with keys:
"topic", "script", "title" (max 60 chars),
"description" (2-3 sentences ending with "Fiction and speculation." plus 3 hashtags including #Shorts),
"tags" (list of 8 short strings), "visual_keywords" (list of 6 English words).
"""

def main():
    r = requests.post(
        URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": PROMPT}],
            "temperature": 1.0,
        },
        timeout=120,
    )
    if r.status_code != 200:
        print("GROQ XATO:", r.status_code, r.text)
        r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", text, re.S)
    data = json.loads(match.group(0))
    with open("script.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
