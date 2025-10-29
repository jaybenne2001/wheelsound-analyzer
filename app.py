import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import json
from utils.audio_tools import live_spectrogram
from utils.capture import record_with_speed
from utils.plotting import plot_spectrogram_matplotlib, plot_speed_matplotlib
from utils.io import write_session_meta, list_sessions, load_audio_sr, compute_spectrogram, align_speed_series
from analyze import analyze_session, classify_simple
import plotly.graph_objects as go

st.set_page_config(page_title="WheelSound Analyzer", layout="wide")

st.title("WheelSound Analyzer")

tab_monitor, tab_capture, tab_analyze, tab_sessions, tab_settings, tab_help = st.tabs(
    ["Live Monitor", "Live Capture", "Analyze Files", "Sessions", "Settings", "Help"]
)

with tab_monitor:
    st.subheader("Real-time Spectrogram")
    run_time = st.slider("Run time (s)", min_value=10, max_value=180, value=30, step=5)
    max_freq = st.slider("Max frequency shown (Hz)", 500, 4000, 2000, 100)
    use_obd = st.checkbox("Overlay OBD speed", value=True)
    use_gps = st.checkbox("Overlay GPS speed (via gpsd)", value=True)
    if st.button("Start Live Spectrogram"):
        live_spectrogram(run_time=run_time, max_freq=max_freq, use_obd=use_obd, use_gps=use_gps)

with tab_capture:
    st.subheader("Record audio and OBD speed")
    duration = st.slider("Duration (s)", 10, 600, 60, 5)
    session_name = st.text_input("Session name", value=datetime.now().strftime("run_%Y%m%d_%H%M%S"))
    note = st.text_area("Notes", value="Rear-right noise test. 25-45 mph.")

    st.caption("Tip: start the capture right before you roll. End while still.")

    if st.button("Start capture"):
        audio_path, csv_path, meta_path = record_with_speed(duration=duration, session_name=session_name, note=note)
        st.success("Capture complete")
        st.write(f"Audio saved to {audio_path}")
        st.write(f"Speed saved to {csv_path}")
        st.write(f"Metadata saved to {meta_path}")

with tab_analyze:
    st.subheader("Analyze existing files")
    audio = st.file_uploader("Audio WAV", type=["wav"])
    speed = st.file_uploader("Speed CSV (time,speed)", type=["csv"])
    show_speed = st.checkbox("Show speed plot", value=True)
    max_freq2 = st.slider("Max frequency shown (Hz)", 500, 4000, 2000, 100, key="maxf2")
    if audio:
        # Load audio from upload
        import soundfile as sf
        import io as _io
        data, sr = sf.read(_io.BytesIO(audio.read()))
        if data.ndim > 1:
            data = data[:,0]
        t_audio = np.arange(len(data)) / sr
        f, t, Sxx_db = compute_spectrogram(data, sr)

        st.pyplot(plot_spectrogram_matplotlib(f, t, Sxx_db, max_freq=max_freq2))

        speed_interp = None
        if speed:
            df = pd.read_csv(speed)
            speed_interp = align_speed_series(t_audio, df)
            if show_speed and speed_interp is not None:
                st.pyplot(plot_speed_matplotlib(t_audio, speed_interp))

        # Run analysis
        res = analyze_session(data, sr, t_audio, speed_interp)
        st.json(res, expanded=False)

        # Simple classification
        label, reasons = classify_simple(res)
        st.markdown(f"**Classifier hint:** {label}")
        with st.expander("Why"):
            for r in reasons:
                st.markdown(f"- {r}")

        # Export report
        if st.button("Export HTML report"):
            from utils.report import export_html_report
            out_path = export_html_report(res, label, reasons)
            st.success(f"Report saved: {out_path}")

with tab_sessions:
    st.subheader("Previous sessions")
    items = list_sessions()
    if not items:
        st.info("No sessions yet. Use Live Capture to create one.")
    else:
        for meta in items:
            st.markdown(f"**{meta.get('session_name','')}**  [{meta.get('timestamp','')}]")
            st.caption(meta.get("note",""))
            cols = st.columns(3)
            with cols[0]:
                if st.button("Open spectrogram", key=f"open_{meta['session_name']}"):
                    # Load files and draw
                    import soundfile as sf
                    data, sr = sf.read(meta["audio_path"])
                    if data.ndim > 1:
                        data = data[:,0]
                    f, t, Sxx_db = compute_spectrogram(data, sr)
                    st.pyplot(plot_spectrogram_matplotlib(f, t, Sxx_db, max_freq=2000))
            with cols[1]:
                if st.button("Analyze", key=f"an_{meta['session_name']}"):
                    import soundfile as sf
                    data, sr = sf.read(meta["audio_path"])
                    if data.ndim > 1:
                        data = data[:,0]
                    t_audio = np.arange(len(data)) / sr
                    import pandas as pd
                    df = pd.read_csv(meta["speed_path"]) if Path(meta["speed_path"]).exists() else None
                    speed_interp = align_speed_series(t_audio, df) if df is not None else None
                    res = analyze_session(data, sr, t_audio, speed_interp)
                    st.json(res, expanded=False)
            with cols[2]:
                st.write(f"Audio: {meta['audio_path']}")
                st.write(f"Speed: {meta['speed_path']}")

with tab_settings:
    st.subheader("Settings")
    st.caption("No persistent settings yet.")

with tab_help:
    st.subheader("How to use")
    st.markdown('''
1. Live Monitor shows a live spectrogram from the mic.
2. Live Capture records audio and OBD speed together for a set time.
3. Analyze Files lets you upload audio and speed logs to visualize and classify a run.
4. Sessions lists your saved runs for quick review.
''')
