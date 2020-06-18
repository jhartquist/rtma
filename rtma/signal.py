# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_signal.ipynb (unless otherwise specified).

__all__ = ['gen_sinusoid', 'plot']

# Cell
from .imports import *
from .core import *

# Cell
def gen_sinusoid(amp = 0.5,
                 freq = 440.0,
                 len_seconds = None,
                 num_samples = None,
                 sample_rate = 44100,
                 phi = 0.0):
    if num_samples is None and len_seconds is not None:
        num_samples = len_seconds * sample_rate
    if num_samples is None:
        num_samples = sample_rate

    if isinstance(freq, list):
        freq = np.linspace(freq[0], freq[1], num_samples)

    n = np.arange(num_samples)
    x = amp * np.cos(2.0 * np.pi * freq * n / sample_rate + phi)
    return x

# Cell
def plot(x, figsize=(10, 2)):
    fig, ax = plt.subplots(1, figsize=figsize)
    ax.plot(x)
    return ax