import json, os, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from common import split_sentences

W, H = 1080, 1920
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


data = json.load(open("script.json", encoding="utf-8"))
script = data["script"]

# 1. narration
gTTS(text=script, lang="en").save("voice.mp3")
dur = float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=nw=1:nk=1", "voice.mp3"]).decode().strip())

# 2. scenes: one per sentence, time split by word count
sentences = split_sentences(script)
words = [max(1, len(s.split())) for s in sentences]
total = sum(words)
index = {}
if os.path.exists("clips/index.json"):
    index = json.load(open("clips/index.json"))

os.makedirs("frames", exist_ok=True)
os.makedirs("scenes", exist_ok=True)
font = ImageFont.truetype(BOLD, 70)
small = ImageFont.truetype(BOLD, 40)


def caption_png(text, path):
    """Transparent 1080x1920 overlay: subtitle box in the lower third + channel name."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = textwrap.wrap(text, width=20)
    lh = 92
    box_h = len(lines) * lh + 70
    y0 = int(H * 0.70)
    d.rounded_rectangle((50, y0, W - 50, y0 + box_h), radius=28, fill=(0, 0, 0, 170))
    d.rectangle((50, y0, 62, y0 + box_h), fill=(200, 30, 30, 255))
    y = y0 + 35 + lh // 2
    for line in lines:
        d.text((W / 2, y), line, font=font, fill=(245, 245, 245, 255), anchor="mm",
               stroke_width=3, stroke_fill=(0, 0, 0, 255))
        y += lh
    d.text((W / 2, H - 110), "APOCALYPSE SECRETS", font=small, fill=(200, 30, 30, 255), anchor="mm")
    d.rectangle((0, 0, W, 12), fill=(200, 30, 30, 255))
    d.rectangle((0, H - 12, W, H), fill=(200, 30, 30, 255))
    img.save(path)


# dark, desaturated, blood-red tinted look applied to every clip
GRADE = ("scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps=30,"
         "eq=brightness=-0.10:contrast=1.15:saturation=0.55,"
         "colorbalance=rs=0.18:gs=-0.04:bs=-0.12:rm=0.10,vignette=PI/4,format=yuv420p").format(w=W, h=H)

scene_files = []
for i, s in enumerate(sentences):
    sec = max(0.8, dur * words[i] / total)
    cap = f"frames/{i:03d}.png"
    caption_png(s, cap)
    out = f"scenes/{i:03d}.mp4"
    clip = index.get(str(i))
    if clip and os.path.exists(clip):
        # real stock footage, looped if shorter than the sentence
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", clip, "-i", cap,
             "-filter_complex", f"[0:v]{GRADE}[bg];[bg][1:v]overlay=0:0,format=yuv420p[v]",
             "-map", "[v]", "-t", f"{sec:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "23", out])
    else:
        # fallback: dark film-grain background with a slow red pulse, no stock needed
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0b0b0b:s={W}x{H}:r=30", "-i", cap,
             "-filter_complex",
             "[0:v]noise=alls=7:allf=t,"
             "eq=brightness='0.025*sin(2*PI*t/3.5)':eval=frame,"
             "colorbalance=rs=0.05:rm=0.03,vignette=PI/3.5,format=yuv420p[bg];"
             "[bg][1:v]overlay=0:0,format=yuv420p[v]",
             "-map", "[v]", "-t", f"{sec:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "23", out])
    scene_files.append(out)

# 3. join scenes and add narration
with open("scenes.txt", "w") as f:
    for p in scene_files:
        f.write(f"file '{p}'\n")
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "scenes.txt", "-i", "voice.mp3",
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
     "-shortest", "-movflags", "+faststart", "video.mp4"])
print(f"video.mp4 ready: {sum(1 for i in range(len(sentences)) if index.get(str(i)))} "
      f"of {len(sentences)} scenes use stock footage")
