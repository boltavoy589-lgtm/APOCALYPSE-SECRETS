name: APOCALYPSE SECRETS Video

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  make:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install FFmpeg
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg
          ffmpeg -version
          ffprobe -version

      - name: Install Python packages
        run: pip install requests gTTS Pillow moviepy

      - name: Generate script
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
        run: python generate_script.py

      - name: Create video
        run: python make_video.py

      - name: Upload generated files
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: apocalypse-secrets-video
          path: |
            *.mp4
            script.json
          if-no-files-found: warn
