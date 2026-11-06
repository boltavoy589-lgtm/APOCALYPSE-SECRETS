# Guts — zombi apokalipsisi, 1-kun (o'zbekcha)

- `guts-1-kun-jonli.mp4` — jonlantirilgan video (soch tebranishi, ko'z qisish, yorug'lik va chang effektlari), ovozsiz diktor.
- `guts-1-kun-subtitr.srt` — 24 ta subtitr satri, aniq vaqtlari bilan.
- `narrate.py` — subtitrlarni o'zbekcha ovozga aylantirib, videoga qo'shadi (Edge TTS, zaxirada Google TTS).

## Ovozli videoni olish
GitHub Actions: **Actions → "Guts 1-kun ovoz qo'shish" → Run workflow**. Tayyor `guts-1-kun-ovozli.mp4`
`guts-day1/out/` papkasiga saqlanadi va artifact sifatida ham yuklanadi.

Mahalliy ishga tushirish:
```
pip install edge-tts gTTS
python narrate.py --video guts-1-kun-jonli.mp4 --srt guts-1-kun-subtitr.srt --out out/guts-1-kun-ovozli.mp4
```
Ovozni almashtirish: `UZ_VOICE=uz-UZ-MadinaNeural` (ayol). Tezlik: `UZ_RATE=-10%`.
