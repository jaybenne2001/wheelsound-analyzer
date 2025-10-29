import sounddevice as sd
import numpy as np
import pandas as pd
import wave
import threading
import time
import obd
from pathlib import Path
from .io import write_session_meta

def record_audio(filename, duration, sr=48000):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()
    audio = np.int16(audio * 32767)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())

def stream_speed(duration, csv_path):
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        connection = obd.OBD()  # auto-connect
    except Exception:
        connection = None
    speeds = []
    t0 = time.time()
    while time.time() - t0 < duration:
        ts = time.time() - t0
        if connection and connection.is_connected():
            rsp = connection.query(obd.commands.SPEED)
            val = rsp.value.magnitude if rsp and not rsp.is_null() else 0.0
        else:
            val = 0.0
        speeds.append((ts, val))
        time.sleep(0.1)
    if connection:
        try:
            connection.close()
        except Exception:
            pass
    df = pd.DataFrame(speeds, columns=['time','speed'])
    df.to_csv(csv_path, index=False)

def record_with_speed(duration=60, session_name="run", note=""):
    audio_path = Path("data/recordings") / f"{session_name}.wav"
    csv_path = Path("data/recordings") / f"{session_name}.csv"

    t_audio = threading.Thread(target=record_audio, args=(str(audio_path), duration))
    t_speed = threading.Thread(target=stream_speed, args=(duration, str(csv_path)))
    t_audio.start()
    t_speed.start()
    t_audio.join()
    t_speed.join()

    meta_path = write_session_meta(session_name, audio_path, csv_path, note)
    return str(audio_path), str(csv_path), str(meta_path)
