from pathlib import Path

import customtkinter as ctk


from spm_control.gui.modes import page_helpers
from spm_control.scan import scan_plot_and_analysis as spa


class MainDisplay:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent

        self.figure = None
        self.axes = None
        self.canvas = None
        self.source = None
        self.metadata = {}

        self.mini_display = page_helpers.createFrame(
            parent, "mini_display", [0.1, 0.005, 0.8, 0.99]
        )

    def display_plot(self, figure, axes=None, source=None, metadata=None):
        self.clear()

        if axes is None:
            if not figure.axes:
                raise ValueError("The supplied figure contains no axes.")
            axes = figure.axes[0]

        self.figure = figure
        self.axes = axes
        self.source = source
        self.metadata = metadata or {}

        self.canvas = page_helpers.embedFigure(self.mini_display, figure)
        return self.canvas

    def display_image(self, file_path):
        self.clear()

        page_helpers.displayImage(self.mini_display, file_path)

        self.source = "saved_image"
        self.metadata = {"file_path": Path(file_path)}
    
    def display_text(self, file_path):
        self.clear()

        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            content = file.read()

        text_box = ctk.CTkTextbox(self.mini_display, wrap="word")
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", content)
        text_box.configure(state="disabled")

        self.source = "text"
        self.metadata = {
            "file_path": Path(file_path),
            "text_widget": text_box
        }

    def display_file(self, file_path):
        extension = Path(file_path).suffix.lower()

        if extension == ".png":
            self.display_image(file_path)
        elif extension == ".txt":
            self.display_text(file_path)
        else:
            raise ValueError(f"Unsupported display format: {extension}")

    def clear(self):
        for widget in self.mini_display.winfo_children():
            widget.destroy()

        self.figure = None
        self.axes = None
        self.canvas = None
        self.source = None
        self.metadata = {}

        file_display = getattr(self.app, "file_display", None)

        if file_display is not None:
            file_display.set_secondary_path("")
        # Any new view ends a comparison, so the compared file's path is cleared too

    def has_selectable_plot(self):
        if self.figure is None or self.axes is None or self.canvas is None:
            return False

        try:
            return bool(self.canvas.get_tk_widget().winfo_exists())
        except Exception:
            return False

    def get_active_plot(self):
        if not self.has_selectable_plot():
            raise RuntimeError(
                "The current display is not a selectable plot. "
                "Display a raster image or live scan first."
            )

        return self.canvas, self.axes

    def redraw(self):
        if self.canvas is not None:
            self.canvas.draw_idle()


    def display_selected_file(self, selected_file):
        scan = spa.find_scan_data(selected_file)

        if scan is None:
            self.display_file(selected_file)
            return

        data_path, channel = scan

        if not data_path.exists():
            raise FileNotFoundError(f"Could not find raster data file: {data_path}")

        figure, image, colorbar = spa.display_saved_raster_plot(data_path, channel)

        metadata = {
            "data_file": data_path,
            "channel": channel,
            "image": image,
            "colorbar": colorbar
        }

        if Path(selected_file).suffix.lower() == ".png":
            metadata["image_file"] = Path(selected_file)

        self.display_plot(
            figure=figure,
            axes=image.axes,
            source="saved_raster",
            metadata=metadata
        )

    def display_side_by_side(self, left_file, right_file):
        figures = []

        for selected_file in (left_file, right_file):
            scan = spa.find_scan_data(selected_file)

            if scan is None or not scan[0].exists():
                raise ValueError(f"Not a raster scan with saved data: {selected_file}")

            data_path, channel = scan
            figure, image, colorbar = spa.display_saved_raster_plot(data_path, channel)

            image.axes.set_title(f"{data_path.stem.removesuffix('_scan_data')}\n{image.axes.get_title()}")
            figure.set_layout_engine("tight")
            # Refits labels and colorbar whenever the half-width frame resizes
            figures.append(figure)
        # Both files load before the display is cleared, so a bad file leaves the current view in place

        self.clear()

        left_frame = page_helpers.createFrame(self.mini_display, "left_plot", [0, 0, 0.5, 1])
        right_frame = page_helpers.createFrame(self.mini_display, "right_plot", [0.5, 0, 0.5, 1])

        page_helpers.embedFigure(left_frame, figures[0])
        page_helpers.embedFigure(right_frame, figures[1])

        self.source = "side_by_side"
        # self.figure stays None, so point selection asks for a single plot instead of ignoring one side