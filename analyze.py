import numpy as np
import librosa
from typing import Dict, Any

def band_power(Sxx_db, freqs, low, high):
    mask = (freqs >= low) & (freqs <= high)
    if not np.any(mask):
        return 0.0
    return float(np.mean(Sxx_db[mask,:]))

def dominant_bands(Sxx_db, freqs, bands):
    out = {}
    for name, (lo, hi) in bands.items():
        out[name] = band_power(Sxx_db, freqs, lo, hi)
    return out

def speed_correlation(feature, speed_series):
    if speed_series is None:
        return None
    if len(feature) != len(speed_series):
        x = np.interp(np.linspace(0,1,len(speed_series)), np.linspace(0,1,len(feature)), feature)
    else:
        x = feature
    x = (x - np.mean(x)) / (np.std(x) + 1e-6)
    v = (speed_series - np.mean(speed_series)) / (np.std(speed_series) + 1e-6)
    return float(np.clip(np.dot(x, v) / len(v), -1.0, 1.0))

def analyze_session(audio, sr, t_audio, speed_interp):
    S = np.abs(librosa.stft(audio, n_fft=2048, hop_length=512)) + 1e-10
    Sxx_db = 10*np.log10(S)
    freqs = librosa.fft_frequencies(sr=sr)

    bands = {
        "low_osc": (8, 30),
        "bearing": (100, 300),
        "brake_grind": (250, 800),
        "broadband": (50, 1200)
    }
    band_levels = dominant_bands(Sxx_db, freqs, bands)

    rms = librosa.feature.rms(S=S).flatten()
    rms = (rms - rms.min()) / (rms.max() - rms.min() + 1e-9)

    corr_speed_rms = speed_correlation(rms, speed_interp) if speed_interp is not None else None

    res = {
        "sr": sr,
        "duration_sec": float(len(audio) / sr),
        "bands_db": band_levels,
        "corr_speed_rms": corr_speed_rms,
        "spectrogram_shape": [int(Sxx_db.shape[0]), int(Sxx_db.shape[1])]
    }
    return res

def classify_simple(res: Dict[str, Any]):
    b = res["bands_db"]
    hints = []
    bearing_level = b["bearing"]
    brake_level = b["brake_grind"]
    lowosc_level = b["low_osc"]
    broadband = b["broadband"]
    corr = res.get("corr_speed_rms", None)

    if corr is not None and corr > 0.25 and bearing_level > brake_level:
        label = "Likely rotational hum (bearing-like or diff output)"
        hints.append(f"RMS correlates with speed (r={corr:.2f}).")
        hints.append("Energy concentrated in 100-300 Hz.")
    elif brake_level > bearing_level and brake_level > lowosc_level:
        label = "Likely light brake or shield grind"
        hints.append("Stronger 250-800 Hz band.")
        hints.append("Pattern often independent of brake pedal force when light.")
    elif lowosc_level > bearing_level and corr is not None and corr > 0.15:
        label = "Likely resonance with wheel oscillation"
        hints.append("Low-frequency band elevated 8-30 Hz.")
        hints.append(f"RMS tracks speed (r={corr:.2f}).")
    else:
        label = "Inconclusive. Harmless resonance likely."
        hints.append("No single band dominates clearly.")

    return label, hints
