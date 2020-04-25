# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_core.ipynb (unless otherwise specified).

__all__ = ['load_audio', 'play_audio', 'plot_audio', 'calc_spectrums', 'plot_mag_spectrum']

# Cell
from .imports import *

# Cell
def load_audio(filename: str) -> (np.array, int):
    """
    Load audio as mono.
    return: signal, sample_rate (Hz)
    """
    # TODO: refactor this to not use librosa?
    return librosa.load(filename, sr=None, mono=True, dtype=np.float32)

# Cell
def play_audio(x, sr):
    display(Audio(x, rate=sr, normalize=False))

# Cell
def plot_audio(x: np.array, sr: int, figsize=(14,2)):
    """
    Plot a signal in the time domain.
    """
    t = np.arange(len(x)) / sr
    plt.figure(figsize=figsize)
    plt.xlabel('time (s)')
    plt.ylabel('amplitude')
    plt.ylim([-1, 1])
    plt.plot(t, x)
    plt.show()

# Cell
def calc_spectrums(x: np.array, n_fft: int, hop_length: int, win_length: int) -> (np.array, np.array):
    """
    Calculate the magnitude and phase spectrum of a signal over time.
    """
    X = librosa.stft(x, n_fft=n_fft, win_length=win_length, hop_length=hop_length, pad_mode='constant')
    return np.abs(X), np.angle(X)

# Cell
def plot_mag_spectrum(spectrum, sr, hop_length, min_bin=None, max_bin=None, figsize=(14,6)):
    import librosa.display
    fig, ax = plt.subplots(1, figsize=figsize)
    coords = np.linspace(0, sr, spectrum.shape[0])[min_bin:max_bin]
    spectrum = spectrum[min_bin:max_bin,:]
    librosa.display.specshow(
        spectrum,
        y_coords=coords,
        y_axis='hz',
        x_axis='time',
        sr=sr,
        hop_length=hop_length,
        ax=ax,
    )
    plt.show()