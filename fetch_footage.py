"""Download one short stock clip per scene from Pexels.

Needs the PEXELS_API_KEY secret. Without it (or on any error) this script
does NOT fail: scenes simply get no clip and make_video.py draws a dark
cinematic background instead.
"""
import json, os, sys
import requests
from common import split_sentences

API = "https://api.pexels.com/videos/search"
KEY = os.environ.get("PEXELS_API_KEY", "").strip()
os.makedirs("clips", exist_ok=True)

data = json.load(open("script.json", encoding="utf-8"))
scenes = split_sentences(data["script"])
keywords = [k for k in data.get("visual_keywords", []) if isinstance(k, str) and k.strip()]
if not keywords:
    keywords = ["dark abandoned city", "foggy empty street", "night forest"]

index, credits, used = {}, [], set()

if not KEY:
    print("PEXELS_API_KEY not set: using generated backgrounds only.")
else:
    headers = {"Authorization": KEY}
    for i in range(len(scenes)):
        # try this scene's keyword, then the next ones, until an unused clip is found
        for attempt in range(3):
            q = keywords[(i + attempt) % len(keywords)]
            try:
                r = requests.get(API, headers=headers, timeout=30,
                                 params={"query": q, "orientation": "portrait", "per_page": 15})
                if r.status_code != 200:
                    print(f"scene {i}: Pexels HTTP {r.status_code} for '{q}'")
                    continue
                pick = None
                for v in r.json().get("videos", []):
                    if v["id"] in used:
                        continue
                    files = [f for f in v.get("video_files", [])
                             if f.get("file_type") == "video/mp4" and f.get("width") and f.get("height")]
                    # prefer portrait files around 720-1080 px wide
                    files = [f for f in files if f["height"] >= f["width"] and 540 <= f["width"] <= 1100]
                    if files:
                        files.sort(key=lambda f: abs(f["width"] - 1080))
                        pick = (v, files[0])
                        break
                if not pick:
                    continue
                v, f = pick
                dl = requests.get(f["link"], timeout=120)
                if dl.status_code != 200 or len(dl.content) < 50_000:
                    continue
                path = f"clips/{i:03d}.mp4"
                with open(path, "wb") as out:
                    out.write(dl.content)
                used.add(v["id"])
                index[str(i)] = path
                name = (v.get("user") or {}).get("name", "unknown")
                credits.append(f"{name} - {v.get('url', 'https://www.pexels.com')}")
                print(f"scene {i}: '{q}' -> {path}")
                break
            except Exception as e:  # network problems must not stop the pipeline
                print(f"scene {i}: error for '{q}': {type(e).__name__}")

json.dump(index, open("clips/index.json", "w"))
with open("credits.txt", "w", encoding="utf-8") as f:
    f.write("Stock video from Pexels (https://www.pexels.com):\n")
    f.write("\n".join(sorted(set(credits))) + "\n" if credits else "(no stock clips used)\n")
print(f"{len(index)}/{len(scenes)} scenes have stock clips")
sys.exit(0)
