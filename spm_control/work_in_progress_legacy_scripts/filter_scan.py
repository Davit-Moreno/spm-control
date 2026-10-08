import numpy as np
from copy import copy
from matplotlib.figure import Figure
from matplotlib import cm

from spm_control.work_in_progress_legacy_scripts import scan_plot_and_analysis as spa
from spm_control.scan.scan_plot_and_analysis import pixel_extent
import spm_control.core_config as core_config


def create_filtered_scan_plot(file_path, channel):
    scan_settings = core_config.load_named_settings("scan", core_config.SCAN_CONFIG)

    intensity_min = scan_settings["intensity_min"]
    intensity_max = scan_settings["intensity_max"]

    Xs, Ys, Ts, ch1, ch2 = spa.load_scan_data(file_path)

    channel = int(channel)

    if channel == 1:
        intensities = ch1
    elif channel == 2:
        intensities = ch2
    elif channel == 0:
        intensities = ch1 + ch2
    else:
        raise ValueError("Channel must be 0, 1, or 2.")
    
    lower = np.min(intensities) if intensity_min in ("", None) else float(intensity_min)
    upper = np.max(intensities) if intensity_max in ("", None) else float(intensity_max)

    filtered = np.ma.masked_outside(intensities, lower, upper)

    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111)

    cmap = copy(cm.viridis)
    cmap.set_bad(color="#303030")

    plot = ax.imshow(
        filtered.T,
        origin="lower",
        extent=pixel_extent((Xs.min(), Xs.max()), (Ys.min(), Ys.max()), Xs.shape),
        cmap=cmap,
        vmin=lower,
        vmax=upper,
        interpolation="none",
        aspect="equal"
    )

    ax.set_xlabel("X (µm)")
    ax.set_ylabel("Y (µm)")
    ax.set_title("Combined Channels" if channel == 0 else f"Channel {channel}")

    fig.colorbar(plot, ax=ax, label="Intensity (counts/s)")
    fig.tight_layout()

    return fig