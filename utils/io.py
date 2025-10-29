from pathlib import Path
import json
import numpy as np
import pandas as pd
import soundfile as sf

DATA_DIR = Path("data/recordings")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def write_session_meta(session_name, audio_path, speed_path, note):
    meta = {
        "session_name": session_name,
        "audio_path": str(audio_path),
        "speed_path": str(speed_path),
        "note": note,
        "timestamp": __import__("datetime").datetime.now().isoformat(timespec="seconds")
    }
    meta_path = DATA_DIR / f"{session_name}.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta_path

def list_sessions():
    out = []
    for p in DATA_DIR.glob("*.json"):
        try:
            out.append(json.loads(p.read_text()))
        except Exception:
            pass
    out.sort(key=lambda x: x.get("timestamp",""))
    return out

def load_audio_sr(path):
    data, sr = sf.read(path)
    if data.ndim > 1:
        data = data[:,0]
    t_audio = np.arange(len(data)) / sr
    return data, sr, t_audio

def compute_spectrogram(y, sr):
    from scipy.signal import spectrogram
    f, t, Sxx = spectrogram(y, fs=sr, nperseg=2048, noverlap=1024)
    Sxx_db = 10*np.log10(Sxx + 1e-10)
    return f, t, Sxx_db

def align_speed_series(t_audio, df_speed):
    if df_speed is None:
        return None
    cols = [c.strip().lower() for c in df_speed.columns]
    df_speed.columns = cols
    if "time" not in cols or "speed" not in cols:
        raise ValueError("CSV must have columns time and speed")
    t = df_speed["time"].values
    v = df_speed["speed"].values
    import numpy as np
    return np.interp(t_audio, t, v)
