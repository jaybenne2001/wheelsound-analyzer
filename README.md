# WheelSound Analyzer

A local Streamlit app to capture, visualize, and analyze subtle wheel-related noises against vehicle speed.

## Features
- Live spectrogram monitor from the laptop mic.
- Live capture of audio and OBD-II speed with aligned timestamps.
- Post-drive analysis: spectrograms, peak tracking, and speed correlation.
- Lightweight rule classifier to hint at likely source.
- Session manager with notes and JSON metadata.
- One-click HTML report export.
- Works offline. No cloud needed.

## Quick start
```bash
pip install -r requirements.txt
streamlit run app.py
```
Use an ELM327-compatible adapter for live speed (Veepeak BLE+, OBDLink CX, etc.).
If OBD is not connected, the app still records audio and falls back to a dummy speed channel.

## Data formats
- Audio: 48 kHz mono WAV
- Speed log: CSV with columns time,speed (seconds, mph)
- Session metadata: JSON in data/recordings
