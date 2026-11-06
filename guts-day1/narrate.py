#!/usr/bin/env python3
"""Guts 1-kun: SRT subtitrlarini o'zbekcha ovozga aylantirib, videoga qo'shadi.

Ishlatish:
    pip install edge-tts gTTS
    python narrate.py --video guts-1-kun-jonli.mp4 --srt guts-1-kun-subtitr.srt --out out/guts-1-kun-ovozli.mp4

Ovoz vositalari (TTS_ENGINE muhit o'zgaruvchisi, standart: auto):
    edge   - Microsoft Edge TTS, uz-UZ-SardorNeural (erkak) / uz-UZ-MadinaNeural (ayol)
    gtts   - Google TTS, 'uz'
    dummy  - faqat sinov uchun (oddiy ton), haqiqiy ovoz emas
auto: avval edge, bo'lmasa gtts.
"""
import argparse, asyncio, os, re, subprocess, sys, tempfile

MAX_SPEEDUP = 1.35          # ovoz satr oynasiga sig'masa, eng ko'pi bilan shuncha tezlashtiriladi
BG_VOLUME = 0.30            # asl musiqa/ovoz diktor ostida
VOICE_VOLUME = 1.6


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.exit(f"Xato: {' '.join(cmd[:3])}...\n{r.stderr[-800:]}")
    return r.stdout


def parse_srt(path):
    cues = []
    blocks = re.split(r"\n\s*\n", open(path, encoding="utf-8").read().strip())
    for b in blocks:
        lines = b.strip().splitlines()
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1])
        t = lambda h, mi, s, ms: int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 1000
        cues.append((t(*m.groups()[:4]), t(*m.groups()[4:]), " ".join(lines[2:]).strip()))
    return cues


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=nw=1:nk=1", path]).strip())


def tts_edge(text, out):
    import edge_tts
    voice = os.environ.get("UZ_VOICE", "uz-UZ-SardorNeural")
    asyncio.run(edge_tts.Communicate(text, voice, rate=os.environ.get("UZ_RATE", "-3%")).save(out))


def tts_gtts(text, out):
    from gtts import gTTS
    gTTS(text=text, lang="uz").save(out)


def tts_dummy(text, out):
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
         f"sine=frequency=220:duration={max(1.0, len(text) * 0.07):.2f}", out])


def synth(text, out):
    order = {"edge": [tts_edge], "gtts": [tts_gtts], "dummy": [tts_dummy]}.get(
        os.environ.get("TTS_ENGINE", "auto"), [tts_edge, tts_gtts])
    last = None
    for fn in order:
        try:
            fn(text, out)
            if os.path.exists(out) and os.path.getsize(out) > 500:
                return fn.__name__
        except Exception as e:  # keyingi vositaga o'tamiz
            last = e
            print(f"  {fn.__name__} ishlamadi: {e}", file=sys.stderr)
    sys.exit(f"Hech bir ovoz vositasi ishlamadi: {last}")


def atempo_chain(x):
    parts = []
    while x > 2.0:
        parts.append("atempo=2.0"); x /= 2.0
    parts.append(f"atempo={x:.4f}")
    return ",".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--srt", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cues = parse_srt(a.srt)
    tmp = tempfile.mkdtemp()
    fitted = []
    for i, (s, e, text) in enumerate(cues, 1):
        raw = os.path.join(tmp, f"r{i:02d}.mp3")
        eng = synth(text, raw)
        d, win = duration(raw), e - s
        wav = os.path.join(tmp, f"v{i:02d}.wav")
        speed = min(d / win, MAX_SPEEDUP) if d > win else 1.0
        run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", atempo_chain(speed) if speed > 1.001 else "anull",
             "-ar", "44100", "-ac", "2", wav])
        print(f"[{i:02d}] {eng} {d:.1f}s/{win:.1f}s x{speed:.2f}  {text[:50]}")
        fitted.append((s, wav))
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.video]
    for _, w in fitted:
        cmd += ["-i", w]
    f = [f"[0:a]volume={BG_VOLUME}[bg]"]
    labels = ["[bg]"]
    for i, (s, _) in enumerate(fitted, 1):
        ms = int(s * 1000)
        f.append(f"[{i}:a]volume={VOICE_VOLUME},adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    f.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.95[out]")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    cmd += ["-filter_complex", ";".join(f), "-map", "0:v", "-map", "[out]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out]
    run(cmd)
    print("Tayyor:", a.out, f"({duration(a.out):.1f}s)")


if __name__ == "__main__":
    main()
