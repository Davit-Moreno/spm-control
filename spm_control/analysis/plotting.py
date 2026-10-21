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

TTTR_PLOT_NAMES = {
    "intensity": "intensityplot.png",
    "g1": "trplplot.png",
    "g2": "g2plot.png"
}
# Same file names the old plotting scripts saved into the .run folders

def plot_save_path(result_file, key):
    return Path(result_file).parent / TTTR_PLOT_NAMES[key]

def load_g1(g1_file, subtract_background=True, background_points=10, background_from="end", normalize=True, align_peak=True):
    """
    Reads a g1 (trPL) file into times, counts and count errors for each channel,
    plus "sum": both SPADs added bin by bin. The background is the mean of the first
    or last background_points, and align_peak moves the peak to t = 0
    """
    data = np.atleast_2d(np.genfromtxt(g1_file, delimiter=","))

    if data.shape[1] != 4:
        raise ValueError(f"expected channel, bin start, bin end and counts columns in the g1 file but found {data.shape[1]}")

    channel, bin_start, bin_end, counts = data.T
    times = (bin_start + bin_end) / 2 / 1000
    # Bin edges are in ps, times are in ns at the middle of each bin

    numbers = np.unique(channel).astype(int)
    raw = {number: (times[channel == number], counts[channel == number]) for number in numbers}

    if all(np.array_equal(raw[number][0], raw[numbers[0]][0]) for number in numbers):
        raw["sum"] = (raw[numbers[0]][0], sum(raw[number][1] for number in numbers))
    # Both SPADs see the same emitter through the beam splitter, so adding them bin by bin gives one decay with more counts

    decays = {}

    for key, (key_times, decay) in raw.items():
        sigma = np.sqrt(np.maximum(decay, 1))
        # Photon counts have √N noise, kept so the fit can weight each point

        if subtract_background and background_points > 0:
            region = decay[-background_points:] if background_from == "end" else decay[:background_points]
            decay = decay - region.mean()
        # The end is after the decay has died out and the start is before the pulse arrives, both are only background

        if normalize and decay.max() > 0:
            sigma = sigma / decay.max()
            decay = decay / decay.max()

        decays[key] = (key_times, decay, sigma)

    if align_peak and decays:
        reference = "sum" if "sum" in decays else next(iter(decays))
        peak_time = decays[reference][0][np.argmax(decays[reference][1])]
        decays = {key: (t - peak_time, decay, sigma) for key, (t, decay, sigma) in decays.items()}
    # Everything shifts by the summed decay's peak so the channels and the sum stay lined up

    return decays

def channel_name(key):
    return "Ch. 0 + Ch. 1" if key == "sum" else f"Ch. {key}"

def mono_exp(t, A, tau, B):
    return A * np.exp(-t / tau) + B

def bi_exp(t, A1, tau1, A2, tau2, B):
    return A1 * np.exp(-t / tau1) + A2 * np.exp(-t / tau2) + B
# B is whatever background is left, without it the slow lifetime absorbs the background and comes out far too long

def fit_decay(times, decay, sigma, model, fit_start=None, fit_end=None):
    """
    Fits a mono or bi-exponential decay from fit_start (default: the peak)
    to fit_end (default: the last point), times are in ns
    """
    try:
        from scipy.optimize import curve_fit
    except ImportError:
        raise ValueError("scipy isn't installed, run  ..\\.venv\\Scripts\\python.exe -m pip install -e .  in spm-control") from None
    # Imported here so the rest of the app still starts if scipy isn't installed

    start = times[np.argmax(decay)] if fit_start is None else fit_start
    end = times[-1] if fit_end is None else fit_end

    window = (times >= start) & (times <= end)
    t = times[window] - start
    y = decay[window]
    weights = sigma[window]

    if len(t) < 6:
        raise ValueError(f"only {len(t)} points between {start:g} and {end:g} ns, at least 6 are needed")

    background = np.median(y[-max(len(y) // 4, 1):])
    amplitude = max(y[0] - background, 1e-9)
    below = np.nonzero(y - background < amplitude / np.e)[0]
    tau = t[below[0]] if below.size and t[below[0]] > 0 else t[-1] / 5
    # Starting guesses read from the data: the tail for the background, where the decay falls to 1/e for τ

    if model == "mono":
        popt, pcov = curve_fit(
            mono_exp, t, y,
            p0=[amplitude, tau, background],
            sigma=weights,
            bounds=([0, 1e-3, -np.inf], [np.inf, np.inf, np.inf]),
            maxfev=20000
        )
        curve = mono_exp(t, *popt)
        params = {"A": popt[0], "tau": popt[1], "B": popt[2]}
        names = ["A", "tau", "B"]
    else:
        popt, pcov = curve_fit(
            bi_exp, t, y,
            p0=[0.7 * amplitude, tau / 3, 0.3 * amplitude, 3 * tau, background],
            sigma=weights,
            bounds=([0, 1e-3, 0, 1e-3, -np.inf], [np.inf, np.inf, np.inf, np.inf, np.inf]),
            maxfev=20000
        )
        curve = bi_exp(t, *popt)
        params = {"A1": popt[0], "tau1": popt[1], "A2": popt[2], "tau2": popt[3], "B": popt[4]}
        names = ["A1", "tau1", "A2", "tau2", "B"]

    errors = dict(zip(names, np.sqrt(np.abs(np.diag(pcov)))))

    if model == "bi" and params["tau1"] > params["tau2"]:
        params["A1"], params["tau1"], params["A2"], params["tau2"] = params["A2"], params["tau2"], params["A1"], params["tau1"]
        errors["A1"], errors["tau1"], errors["A2"], errors["tau2"] = errors["A2"], errors["tau2"], errors["A1"], errors["tau1"]
    # The fast lifetime is always tau1

    return {
        "model": model,
        "start": start,
        "end": end,
        "params": params,
        "errors": errors,
        "times": t + start,
        "curve": curve,
        "residuals": y - curve
    }

def describe_fit(fit):
    p = fit["params"]

    if fit["model"] == "mono":
        return f"τ = {p['tau']:.2f} ns"

    fast = p["A1"] / (p["A1"] + p["A2"])
    return f"τ₁ = {p['tau1']:.2f} ns ({fast:.0%}), τ₂ = {p['tau2']:.2f} ns ({1 - fast:.0%})"

def create_g1_plot(
    g1_file,
    title="trPL",
    channels=(0, 1),
    fits=(),
    fit_start=None,
    fit_end=None,
    subtract_background=True,
    background_points=10,
    background_from="end",
    normalize=True,
    align_peak=True,
    residuals=False
):
    """
    Plots the trPL decay of each channel with optional mono and bi-exponential fits.
    Returns the figure and the fit results so they can be saved
    """
    decays = load_g1(g1_file, subtract_background, background_points, background_from, normalize, align_peak)

    fig = Figure(dpi=100, layout="tight")

    if residuals and fits:
        ax, residual_ax = fig.subplots(2, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    else:
        ax = fig.add_subplot(111)
        residual_ax = None

    colors = {0: ("blue", "navy"), 1: ("red", "darkred"), "sum": ("dimgray", "black")}
    line_styles = {"mono": "--", "bi": "-"}
    results = []

    for key in channels:
        if key not in decays:
            if key == "sum":
                raise ValueError("the SPADs in this g1 file don't share the same time bins, so they can't be added")
            continue

        times, decay, sigma = decays[key]
        color, dark = colors.get(key, ("grey", "black"))
        shown = decay > 0

        ax.plot(times[shown], decay[shown], "o", ms=3, color=color, alpha=0.6, label=channel_name(key))
        # Points at or below zero can't be drawn on a log axis

        for model in fits:
            try:
                fit = fit_decay(times, decay, sigma, model, fit_start, fit_end)
            except (RuntimeError, ValueError) as error:
                ax.plot([], [], line_styles[model], color=dark, label=f"{channel_name(key)} {model}: fit failed")
                results.append({"channel": key, "model": model, "error": str(error)})
                continue
            # A fit that doesn't converge is noted in the legend instead of losing the whole plot

            ax.plot(fit["times"], fit["curve"], line_styles[model], color=dark, lw=2, label=f"{channel_name(key)} {model}: {describe_fit(fit)}")

            if residual_ax is not None:
                residual_ax.plot(fit["times"], fit["residuals"], "o", ms=2, color=dark, alpha=0.7)

            results.append({"channel": key, **fit})

    ax.set_yscale("log")

    if normalize:
        ax.set_ylim(bottom=1e-4)

    ax.set_ylabel("Intensity (norm.)" if normalize else "Counts")
    ax.set_title(title)
    ax.legend(fontsize=8)

    x_label = "Time (ns)" if align_peak else "Time after laser pulse (ns)"

    if residual_ax is not None:
        residual_ax.axhline(0, color="black", lw=1)
        residual_ax.set_ylabel("Residuals")
        residual_ax.set_xlabel(x_label)
    else:
        ax.set_xlabel(x_label)

    return fig, results

def save_fit_results(results, output_path, g1_file):
    lines = [f"trPL fit results for {g1_file}", ""]

    for result in results:
        if "error" in result:
            lines.append(f"{channel_name(result['channel'])} {result['model']}: fit failed ({result['error']})")
            continue

        lines.append(f"{channel_name(result['channel'])} {result['model']}-exponential, fit from {result['start']:g} to {result['end']:g} ns")

        for name, value in result["params"].items():
            unit = " ns" if name.startswith("tau") else ""
            lines.append(f"    {name} = {value:.6g} ± {result['errors'][name]:.2g}{unit}")

    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
