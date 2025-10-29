
import streamlit as st
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
import queue
import time

from .speed import SpeedBuffer, OBDSpeedThread, GPSSpeedThread

def live_spectrogram(run_time=60, max_freq=2000, sr=48000, use_obd=True, use_gps=True):
    q = queue.Queue()
    def audio_callback(indata, frames, time_info, status):
        if status:
            print(status)
        q.put(indata.copy())

    stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=sr)
    stream.start()

    buf = SpeedBuffer()
    threads = []
    if use_obd:
        t_obd = OBDSpeedThread(buf, period=0.1)
        t_obd.start()
        threads.append(t_obd)
    if use_gps:
        t_gps = GPSSpeedThread(buf, period=1.0)
        t_gps.start()
        threads.append(t_gps)

    fig, ax = plt.subplots(figsize=(9,4))
    ax2 = ax.twinx()
    img = st.pyplot(fig)

    window = np.zeros(int(sr*10))
    t0 = time.time()
    while time.time() - t0 < run_time:
        try:
            data = q.get(timeout=1.0)
            data = data.flatten()
            L = len(data)
            window = np.concatenate([window[L:], data])
            f, t, Sxx = spectrogram(window, fs=sr, nperseg=2048, noverlap=1024)
            ax.clear()
            pcm = ax.pcolormesh(t, f, 10*np.log10(Sxx + 1e-10), shading="auto")
            ax.set_ylim(0, max_freq)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Frequency (Hz)")
            ax.set_title("Live Spectrogram with Speed Overlay")

            samples = buf.get()
            if samples and len(t) > 1:
                ts, mph = np.array(samples).T
                t_span = t[-1]
                rel_ts = ts - ts.max() + t_span
                mask = (rel_ts >= 0) & (rel_ts <= t_span)
                if np.any(mask):
                    rel_ts = rel_ts[mask]
                    mph = mph[mask]
                    if len(mph) > 3:
                        from scipy.ndimage import uniform_filter1d
                        mph_s = uniform_filter1d(mph, size=min(10, len(mph)))
                    else:
                        mph_s = mph
                    ax2.clear()
                    ax2.plot(rel_ts, mph_s, color="white", alpha=0.85, linewidth=1.5)
                    ax2.set_ylabel("Speed (mph)")
                    ax2.set_ylim(0, max(5.0, float(np.nanmax(mph_s) * 1.2)))
                else:
                    ax2.clear()
                    ax2.set_ylabel("Speed (mph)")
            img.pyplot(fig)
        except queue.Empty:
            pass

    stream.stop()
    stream.close()
    for th in threads:
        th.stop()
    st.success("Live monitoring ended.")
