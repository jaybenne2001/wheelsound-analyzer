import matplotlib.pyplot as plt

def plot_spectrogram_matplotlib(f, t, Sxx_db, max_freq=2000):
    fig, ax = plt.subplots(figsize=(10,4))
    pcm = ax.pcolormesh(t, f, Sxx_db, shading="auto")
    ax.set_ylim(0, max_freq)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title("Spectrogram (dB)")
    fig.colorbar(pcm, ax=ax, label="dB")
    return fig

def plot_speed_matplotlib(t_audio, speed_interp):
    fig, ax = plt.subplots(figsize=(10,2))
    ax.plot(t_audio, speed_interp)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Speed (mph)")
    ax.set_title("Speed")
    return fig
