import numpy as np
from copy import copy
from matplotlib.figure import Figure
from matplotlib import cm
from matplotlib.colors import Normalize


def pixel_extent(xlim, ylim, shape):
    """
    Widens the first and last scan positions by half a pixel on each side,
    so every pixel is centered on the position it was measured at
    """
    x_count, y_count = shape

    x_half = (xlim[1] - xlim[0]) / (2 * (x_count - 1)) if x_count > 1 else 0.5
    y_half = (ylim[1] - ylim[0]) / (2 * (y_count - 1)) if y_count > 1 else 0.5
    # A single row or column has no step to measure, so it gets a 1 µm wide pixel

    return (xlim[0] - x_half, xlim[1] + x_half, ylim[0] - y_half, ylim[1] + y_half)

def create_live_raster_plot(xlim, ylim, shape, vmin=None, vmax=None):
    fig = Figure(dpi=100)
    ax = fig.add_subplot(111)

    cmap = copy(cm.viridis)
    cmap.set_bad(color="#303030")

    initial_data = np.ma.masked_invalid(np.full(shape, np.nan))

    image = ax.imshow(
        initial_data.T,
        origin="lower",
        extent=pixel_extent(xlim, ylim, shape),
        cmap=cmap,
        norm=Normalize(vmin=vmin, vmax=vmax),
        interpolation="none",
        aspect="equal"
    )

    ax.set_xlabel("X (µm)")
    ax.set_ylabel("Y (µm)")
    ax.set_title("Combined Channels")

    colorbar = fig.colorbar(image, ax=ax, label="Intensity (counts/s)")
    fig.tight_layout()

    return fig, image, colorbar

def update_live_raster_plot(fig, image, colorbar, intensities):
    displayed = np.asarray(intensities, dtype=float)
    image.set_data(displayed.T)

    valid = displayed[np.isfinite(displayed)]

    if valid.size:
        new_min = 0.0
        new_max = float(valid.max())

        if new_min == new_max:
            new_min = 0
            new_max = max(new_max, 1)

        image.set_clim(new_min, new_max)
        colorbar.update_normal(image)

    fig.canvas.draw_idle()

def save_raster_plot(intensities, x_nodes, y_nodes, output_path, title):
    fig = Figure(figsize=(7, 7), dpi=100)
    ax = fig.add_subplot(111)

    valid = intensities[np.isfinite(intensities)]
    vmax = max(float(valid.max()), 1) if valid.size else 1

    image = ax.imshow(
        intensities.T,
        origin="lower",
        extent=pixel_extent((x_nodes[0], x_nodes[-1]), (y_nodes[0], y_nodes[-1]), intensities.shape),
        vmin=0,
        vmax=vmax,
        interpolation="none",
        aspect="equal"
    )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(title)

    fig.colorbar(image, ax=ax, label="Intensity")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")



def display_saved_raster_plot(file_path, channel=0, vmin=None, vmax=None):
    data = np.loadtxt(file_path, dtype=float, delimiter=",")

    if data.ndim == 1:
        data = data.reshape(1, -1)

    if data.shape[1] < 5:
        raise ValueError("Scan data must contain X, Y, Z, channel 1, and channel 2.")

    xs = data[:, 0]
    ys = data[:, 1]
    ch1 = data[:, 3]
    ch2 = data[:, 4]

    reset_indices = np.where(np.diff(ys) < 0)[0]

    if reset_indices.size:
        y_count = int(reset_indices[0] + 1)
    else:
        raise ValueError("Could not determine the raster dimensions from the scan data.")

    point_count = len(data)

    if point_count % y_count != 0:
        raise ValueError(
            f"Scan contains {point_count} points, which cannot be reshaped "
            f"using {y_count} Y positions."
        )

    x_count = point_count // y_count
    shape = (x_count, y_count)

    x_grid = xs.reshape(shape)
    y_grid = ys.reshape(shape)
    ch1_grid = ch1.reshape(shape)
    ch2_grid = ch2.reshape(shape)

    if channel == 0:
        intensities = ch1_grid + ch2_grid
        title = "Combined Channels"
    elif channel == 1:
        intensities = ch1_grid
        title = "Channel 1"
    elif channel == 2:
        intensities = ch2_grid
        title = "Channel 2"
    else:
        raise ValueError("Channel must be 0, 1, or 2.")

    xlim = (float(np.nanmin(x_grid)), float(np.nanmax(x_grid)))
    ylim = (float(np.nanmin(y_grid)), float(np.nanmax(y_grid)))

    figure, image, colorbar = create_live_raster_plot(
        xlim=xlim,
        ylim=ylim,
        shape=shape,
        vmin=vmin,
        vmax=vmax
    )

    image.set_data(intensities.T)
    image.axes.set_title(title)

    valid = intensities[np.isfinite(intensities)]

    if valid.size:
        display_min = 0.0 if vmin is None else float(vmin)
        display_max = float(valid.max()) if vmax is None else float(vmax)

        if display_min == display_max:
            display_min = 0
            display_max = max(display_max, 1)

        image.set_clim(display_min, display_max)
        colorbar.update_normal(image)

    figure.canvas.draw_idle()

    return figure, image, colorbar