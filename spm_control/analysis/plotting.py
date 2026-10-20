import numpy as np
from pathlib import Path
from matplotlib.figure import Figure


def find_tttr_results(ptu_file):
    """
    Finds the intensity, g1 and g2 results made from a .ptu measurement,
    results that can't be found are None
    """
    ptu_file = Path(ptu_file)

    if ptu_file.suffix.lower() != ".ptu":
        return None

    g1_run = ptu_file.parent / f"{ptu_file.name}.g1.run"
    g2_run = ptu_file.parent / f"{ptu_file.name}.g2.run"
    # The run folders sit next to the .ptu, e.g. Scan22.ptu.g2.run

    intensity = None

    for run in (g2_run, g1_run):
        if (run / "intensity").exists():
            intensity = run / "intensity"
            break
    # Both run folders hold the same intensity file, so either one works

    return {
        "measurement": ptu_file,
        "intensity": intensity,
        "g1": g1_run / "g1" if (g1_run / "g1").exists() else None,
        "g2": g2_run / "g2" if (g2_run / "g2").exists() else None
    }

def create_intensity_plot(intensity_file, title="Intensity"):
    data = np.atleast_2d(np.genfromtxt(intensity_file, delimiter=","))

    if data.shape[1] < 4:
        raise ValueError("expected bin start, bin end and two channel columns in the intensity file")

    bin_start = data[:, 0]
    bin_end = data[:, 1]
    ch0 = data[:, 2]
    ch1 = data[:, 3]
    # Bin edges are in µs, the first and last bins can be partial

    times = (bin_start + bin_end) / 2 / 1e6
    bin_ms = np.median(bin_end - bin_start) / 1e3

    fig = Figure(dpi=100, layout="tight")
    ax = fig.add_subplot(111)

    ax.plot(times, ch0, color="blue", label="Ch. 0")
    ax.plot(times, ch1, color="red", label="Ch. 1")
    ax.plot(times, ch0 + ch1, color="black", alpha=0.5, label="Sum")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel(f"Intensity (counts/{bin_ms:g} ms)")
    ax.set_title(title)
    ax.legend()

    return fig

def create_g2_plot(g2_file, repetition_rate, title="g2"):
    data = np.atleast_2d(np.genfromtxt(g2_file, delimiter=","))

    if data.shape[1] != 7:
        raise ValueError(
            f"expected a T3 g2 file with 7 columns but found {data.shape[1]}, "
            "T2 g2 files aren't supported by this plot yet"
        )

    channel_1, channel_2, left_pulse, right_pulse, left_bin, right_bin, counts = data.T

    cross = channel_1 != channel_2
    left = cross & np.isclose(left_pulse, -1.5)
    center = cross & np.isclose(left_pulse, -0.5)
    right = cross & np.isclose(right_pulse, 1.5)
    # Cross-correlations between the two detectors, split into the pulse before, the same pulse, and the pulse after

    if not center.any():
        raise ValueError("no center pulse found, the g2 file may not have been processed with pulse limits -1.5 to 1.5")

    side_counts = counts[left].sum() + counts[right].sum()

    if side_counts == 0:
        raise ValueError("no counts in the side pulses, so g2(0) can't be normalized")

    g2_zero = 2 * counts[center].sum() / side_counts
    print(f"g2(0) = {g2_zero:.3f}")

    period = 1e12 / repetition_rate
    bin_center = (left_bin + right_bin) / 2
    # Times are in ps, each point is drawn at the middle of its time bin

    fig = Figure(dpi=100, layout="tight")
    ax = fig.add_subplot(111)

    ax.plot((bin_center[left] - period) / 1000, counts[left], "o", color="grey", alpha=0.3, label="Side Pulses")
    ax.plot((bin_center[right] + period) / 1000, counts[right], "o", color="grey", alpha=0.3)
    ax.plot(bin_center[center] / 1000, counts[center], "o", color="black", label="Center Pulse")

    ax.text(0.03, 0.95, f"$g^{{(2)}}(0) = {g2_zero:.2f}$", transform=ax.transAxes, va="top", fontsize=14)
    # Placed relative to the plot instead of fixed data coordinates, so it stays visible for any data

    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Correlation Counts")
    ax.set_title(title)
    ax.legend(loc="upper right")

    return fig
