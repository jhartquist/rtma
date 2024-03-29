# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/03_stft.ipynb (unless otherwise specified).

__all__ = ['get_cola_window', 'gen_frames', 'synth_frames', 'stft', 'istft']

# Cell
from .imports import *
from .core import *
from .signal import *
from .fft import *

# Cell
def get_cola_window(window_name: str, n_window: int, n_hop: int):
    even_window = n_window % 2 == 0
    window_by_hop = n_window // n_hop

    if (window_name == 'hamming'):
        window = get_window(window_name, n_window, fftbins=even_window)
        if not even_window:
            window[ 0] /= 2
            window[-1] /= 2
        window /= (window_by_hop * 0.54)

    elif (window_name == 'hann' or window_name == 'hanning'):
        window = get_window(window_name, n_window, fftbins=even_window)

    elif (window_name == 'blackman'):
        window = get_window(window_name, n_window, fftbins=even_window)
        window /= (window_by_hop * 0.42)

    n_overlap = n_window - n_hop
    assert check_COLA(window, nperseg=n_window, noverlap=n_overlap)

    return window

# Cell
def gen_frames(x, n_window, n_hop, window = None, pad_center=False):
    if pad_center:
        n_pad = n_window // 2
    else:
        n_overlap = n_window - n_hop
        n_pad = n_overlap

    x = np.pad(x, (n_pad, 0), mode='constant')
    i = 0

    if window is not None:
        window = window / window.sum()

    while i < x.size:
        frame = x[i:i+n_window]
        if frame.size < n_window:
            frame = np.pad(frame, (0, n_window-frame.size), mode='constant')
        if window is not None:
            frame = frame * window
        yield frame
        i += n_hop

# Cell
def synth_frames(frames, n_hop, n_samples: int = None, pad_center=False):
    frames = list(frames)
    n_frames = len(frames) # TODO: make synth_frames a generator ?
    n_window = frames[0].size

    buffer_len = n_window + n_hop*(n_frames-1)
    y = np.zeros(buffer_len, dtype=frames[0].dtype)

    for i, frame in enumerate(frames):
        offset_i = i*n_hop
        y[offset_i:offset_i+n_window] += frame * n_hop

    n_overlap = n_window - n_hop
    if pad_center:
        n_pad = n_window // 2
    else:
        n_pad = n_overlap

    y = y[n_pad:-n_pad]
    if n_samples is not None:
        y = y[:n_samples]
    return y

# Cell
def stft(x, n_fft, n_hop, window, decibels=True, pad_center=False):
    n_window = window.size
    for x_i in gen_frames(x, n_window=n_window, n_hop=n_hop, window=window, pad_center=pad_center):
        m_x, p_x = fft_analysis(x_i, n_fft, decibels=decibels)
        yield m_x, p_x

# Cell
def istft(spectrum, n_hop, n_window, n_samples: int = None, decibels: bool = True, pad_center=False):
    frames = (fft_synthesis(m_x, p_x, n_window, decibels=decibels) for m_x, p_x in spectrum)
    return synth_frames(frames, n_hop, n_samples, pad_center=pad_center)