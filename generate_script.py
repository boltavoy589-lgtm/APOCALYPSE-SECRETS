name: make

# DIQQAT: bu "on:" bo'limini o'zingizdagi eski fayldan nusxalang,
# agar u boshqacha bo'lsa (jadval, push va hokazo).
on:
  workflow_dispatch:

jobs:
  make:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      # Xatoning sababi shu edi: ffprobe (ffmpeg bilan birga) o'rnatilmagan.
      - name: Install ffmpeg
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg
          ffprobe -version

      - name: Install Python dependencies
        run: pip install requests gTTS Pillow

      - name: Generate script
        run: python generate_script.py

      - name: Make video
        run: python make_video.py

      - uses: actions/upload-artifact@v4
        with:
          name: video
          # Pastdagi yo'lni make_video.py tayyor videoni qayerga saqlashiga qarab o'zgartiring.
          path: "*.mp4"
