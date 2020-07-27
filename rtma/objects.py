# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/05_objects.ipynb (unless otherwise specified).

__all__ = ['Signal', 'Frame', 'Analysis', 'SpectralFrame', 'SpectralAnalysis', 'Peak', 'PeakFrame', 'PeakAnalysis',
           'SineTrack', 'SineModelFrame', 'SineModelAnalysis']

# Cell
from .imports import *
from .core import *
from .signal import *
from .fft import *
from .stft import *
from .sine_model import *

# Cell
class Signal:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.x, self.sample_rate = load_audio(filename)

    @property
    def n_samples(self) -> int:
        return self.x.shape[-1]

    @property
    def duration(self) -> float:
        return self.n_samples / self.sample_rate

    def __len__(self) -> int:
        return self.n_samples

    def play(self) -> None:
        play_audio(self.x, self.sample_rate)

    def plot(self, *args, start=None, end=None, **kwargs) -> None:
        x = self.x
        if end is not None:
            x = x[:end]
        if start is not None:
            x = x[start:]
        return plot(x, *args, **kwargs)

    def __str__(self) -> str:
        return f'Signal("{self.filename}")'

    def __repr__(self) -> str:
        return str(self)

# Cell
class Frame:
    def __init__(self, x: np.ndarray, index: int):
        self.x = x
        self.index = index

    def plot(self):
        plot(self.x)

# Cell
class Analysis:
    def __init__(self,
                 signal: Signal,
                 frame_size: int,
                 hop_size: int) -> None:
        self.signal = signal
        self.frame_size = frame_size
        self.hop_size = hop_size

    def __repr__(self) -> str:
        return f'Analysis({self.signal}, frame_size={self.frame_size}, hop_size={self.hop_size})'

    @property
    def overlap(self) -> int:
        return self.frame_size - self.hop_size

    @property
    def frames(self):
        x_pad = np.pad(self.signal.x, (self.overlap, 0), mode='constant')
        offset = 0
        frame_i = 0
        while offset < x_pad.size:
            x_frame = x_pad[offset:offset+self.frame_size]
            if x_frame.size < self.frame_size:
                x_frame = np.pad(x_frame, (0, self.frame_size-x_frame.size), mode='constant')
            yield Frame(x_frame, frame_i)
            offset += self.hop_size
            frame_i += 1

    @property
    def sample_rate(self):
        return self.signal.sample_rate

# Cell
class SpectralFrame(Frame):
    def __init__(self, frame: Frame, window: np.ndarray, fft_size: int):
        assert frame.x.size == window.size
        assert frame.x.size <= fft_size
        assert is_power_of_two(fft_size)
        super().__init__(frame.x * window, frame.index)

        # instance variables
        self.frame = frame
        self.window = window
        self.fft_size = fft_size

        # lazy computed properties
        self._fft_buffer = None
        self._dft = None
        self._magnitudes = None
        self._magnitudes_db = None
        self._phases = None

    @property
    def fft_buffer(self):
        if self._fft_buffer is None:
            self._fft_buffer = zero_phase_buffer(self.x, n_fft=self.fft_size)
        return self._fft_buffer

    @property
    def dft(self):
        if self._dft is None:
            self._dft = np.fft.rfft(self.fft_buffer)
        return self._dft

    @property
    def magnitudes(self):
        if self._magnitudes is None:
            self._magnitudes = abs(self.dft)
        return self._magnitudes

    @property
    def magnitudes_db(self):
        if self._magnitudes_db is None:
            self._magnitudes_db = amplitude_to_decibels(self.magnitudes)
        return self._magnitudes_db

    @property
    def phases(self):
        if self._phases is None:
            dft = self.dft.copy()
            dft.real[abs(dft.real) < EPSILON] = 0.0
            dft.imag[abs(dft.imag) < EPSILON] = 0.0
            self._phases = np.unwrap(np.angle(dft))
        return self._phases

    def plot_magnitudes(self, decibels: bool = True):
        spec = self.magnitudes_db if decibels else self.magnitudes
        return plot(spec)

    def plot_phases(self):
        return plot(self.phases)

# Cell
class SpectralAnalysis(Analysis):
    def __init__(self,
                 *args,
                 fft_size: int,
                 window_name: str,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.fft_size = fft_size
        self.window_name = window_name
        window = get_cola_window(window_name, self.frame_size, self.hop_size)
        self.window = window / window.sum()
        self._magnitudes = None

    @property
    def spectral_frames(self):
        for frame in super().frames:
            yield SpectralFrame(frame, self.window, self.fft_size)

    @property
    def magnitudes(self):
        # dB
        if self._magnitudes is None:
            self._magnitudes = np.stack([f.magnitudes_db for f in self.spectral_frames])
        return self._magnitudes

    def plot_magnitudes(self, max_plot_freq: float, figsize=(12, 6)):
        n_bins = int(self.fft_size * max_plot_freq / self.sample_rate) + 1
        n_frames = self.magnitudes.shape[0]

        frame_times = np.arange(n_frames) / self.sample_rate * self.hop_size
        bin_freqs = np.arange(n_bins) * self.sample_rate / self.fft_size

        fig, ax = plt.subplots(1, figsize=figsize)
        ax.set_xlabel('time (s)')
        ax.set_ylabel('frequency (Hz)')
        ax.set_xlim([0, frame_times[-1]])
        ax.set_ylim([0, bin_freqs[-1]])
        ax.pcolormesh(frame_times, bin_freqs, self.magnitudes.T[:n_bins])
        return ax

# Cell
class Peak:
    def __init__(self, frequency: float, magnitude: float, phase: float):
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase

    def __repr__(self):
        return f'Peak(freq={self.frequency:.2f}, mag={self.magnitude:.2f},phase={self.phase:.2f})'

# Cell
class PeakFrame(SpectralFrame):
    def __init__(self, *args, peak_threshold: float, sample_rate: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.peak_threshold = peak_threshold
        self.sample_rate = sample_rate
        self._peaks = None

    @property
    def peaks(self):
        if self._peaks is None:
            peak_i = detect_peaks(self.magnitudes_db, self.peak_threshold)
            ipeak_i, ipeak_m = interpolate_peaks(self.magnitudes_db, peak_i)
            ipeak_f = ipeak_i * self.sample_rate / self.fft_size
            ipeak_p = np.interp(ipeak_i, np.arange(self.phases.size), self.phases)
            self._peaks = [Peak(f,m,p) for f,m,p in zip(ipeak_f, ipeak_m, ipeak_p)]
        return self._peaks

    def plot_peaks(self):
        ax = self.plot_magnitudes()
        for p in self.peaks:
            idx = p.frequency / self.sample_rate * self.fft_size
            ax.axvline(idx, color='red')


# Cell
class PeakAnalysis(SpectralAnalysis):
    def __init__(self,
                 *args,
                 peak_threshold: float,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.peak_threshold = peak_threshold

    @property
    def peak_frames(self):
        for frame in super().frames:
            yield PeakFrame(frame,
                            window=self.window,
                            fft_size=self.fft_size,
                            peak_threshold=self.peak_threshold,
                            sample_rate=self.sample_rate)

# Cell
class SineTrack:
    def __init__(self, peak: Peak, start_index: int):
        self.peaks = [peak]
        self.start_index = start_index
        self.end_index = None

    @property
    def frequency(self):
        return self.peaks[-1].frequency

    @property
    def magnitude(self):
        return self.peaks[-1].magnitude

    def __len__(self):
        return len(self.peaks)

    def __repr__(self):
        return f'SineTrack(freq={self.frequency}, start={self.start_index}, end={self.end_index}, len={len(self)})'

    def plot(self, ax: plt.Axes, sample_rate: int, hop_size: int):
        xs = np.arange(self.start_index, self.end_index) / sample_rate * hop_size
        ys = [peak.frequency for peak in self.peaks]
        ax.plot(xs, ys, c='k')

# Cell
class SineModelFrame:
    def __init__(self,
                 peak_frame: PeakFrame,
                 previous_tracks: List[SineTrack],
                 freq_dev_offset: float,
                 freq_dev_slope: float):
        self.peak_frame = peak_frame
        self.previous_tracks = previous_tracks
        self.freq_dev_offset = freq_dev_offset
        self.freq_dev_slope = freq_dev_slope
        self._tracks = None
        self.track_peaks = None

    @property
    def index(self):
        return self.peak_frame.index

    @property
    def peaks(self):
        return self.peak_frame.peaks

    @property
    def tracks(self):
        if self._tracks is None:
            cur_peaks = self.peaks.copy()
            cur_freqs = np.array([peak.frequency for peak in cur_peaks])

            prev_tracks = sorted(
                self.previous_tracks.copy(),
                key=lambda t: -t.magnitude
            )

            tracks = []
            for prev_track in prev_tracks:
                if len(cur_peaks) > 0:
                    cur_i = np.argmin(abs(cur_freqs - prev_track.frequency))
                    freq_dev_thresh = self.freq_dev_offset + self.freq_dev_slope * cur_freqs[cur_i]
                    freq_dev = abs(cur_freqs[cur_i] - prev_track.frequency)
                    if freq_dev < freq_dev_thresh:
                        cur_freqs = np.delete(cur_freqs, cur_i)
                        track_peak = cur_peaks.pop(cur_i)
                        prev_track.peaks.append(track_peak)
                        tracks.append(prev_track)
                        continue
                prev_track.end_index = self.index

            for peak in cur_peaks:
                tracks.append(SineTrack(peak, self.index))

            self._tracks = tracks
        return self._tracks

# Cell
class SineModelAnalysis(PeakAnalysis):
    def __init__(self,
                 *args,
                 freq_dev_offset: float = 20.0,
                 freq_dev_slope: float = 0.01,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.freq_dev_offset = freq_dev_offset
        self.freq_dev_slope = freq_dev_slope
        self.all_tracks = None
        self._tracks = None

    @property
    def sine_model_frames(self):
        self.all_tracks = []
        tracks = []
        for peak_frame in super().peak_frames:
            frame = SineModelFrame(peak_frame, tracks, self.freq_dev_offset, self.freq_dev_slope)
            tracks = frame.tracks
            for track in tracks:
                if track.start_index == frame.index:
                    self.all_tracks.append(track)
            yield frame

    @property
    def tracks(self):
        if self._tracks is None:
            self.sine_model_frames
            self._tracks = self.all_tracks.copy()
        return self._tracks

    def plot_sines(self, max_plot_freq: float, figsize=(12, 6)):
        ax = self.plot_magnitudes(max_plot_freq=max_plot_freq, figsize=figsize)
        for track in self.tracks:
            track.plot(ax, self.sample_rate, self.hop_size)