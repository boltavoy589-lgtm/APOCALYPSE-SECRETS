import json, os, re, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

W, H = 1080, 1920
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

data = json.load(open("script.json", encoding="utf-8"))
script = data["script"]

# 1. ovoz
gTTS(text=script, lang="en").save("voice.mp3")
dur = float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=nw=1:nk=1", "voice.mp3"]).decode().strip())

# 2. har gap uchun alohida kadr
sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
words = [max(1, len(s.split())) for s in sentences]
total = sum(words)
os.makedirs("frames", exist_ok=True)
font = ImageFont.truetype(BOLD, 78)
small = ImageFont.truetype(BOLD, 44)

slides = []
for i, s in enumerate(sentences):
    img = Image.new("RGB", (W, H), (12, 12, 12))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 14), fill=(200, 30, 30))
    d.rectangle((0, H - 14, W, H), fill=(200, 30, 30))
    lines = textwrap.wrap(s, width=18)
    y = H // 2 - len(lines) * 55
    for line in lines:
        d.text((W / 2, y), line, font=font, fill=(240, 240, 240), anchor="mm")
        y += 110
    d.text((W / 2, H - 120), "APOCALYPSE SECRETS", font=small, fill=(200, 30, 30), anchor="mm")
    path = f"frames/{i:03d}.png"
    img.save(path)
    slides.append((path, dur * words[i] / total))

# 3. ffmpeg uchun ro'yxat
with open("frames.txt", "w") as f:
    for path, sec in slides:
        f.write(f"file '{path}'\nduration {sec:.2f}\n")
    f.write(f"file '{slides[-1][0]}'\n")

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "frames.txt",
    "-i", "voice.mp3", "-vf", "fps=30,format=yuv420p",
    "-c:v", "libx264", "-c:a", "aac", "-shortest", "video.mp4",
], check=True)
print("video.mp4 tayyor")
