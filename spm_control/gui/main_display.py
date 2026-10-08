from pathlib import Path

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


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

        self.toolbar_frame = ctk.CTkFrame(self.mini_display, fg_color="transparent")
        self.toolbar_frame.pack(side="bottom", fill="x")

        self.canvas_frame = ctk.CTkFrame(self.mini_display, fg_color="transparent")
        self.canvas_frame.pack(side="top", fill="both", expand=True)

        self.canvas = FigureCanvasTkAgg(figure, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.toolbar = NavigationToolbar2Tk(
            self.canvas,
            self.toolbar_frame,
            pack_toolbar=False
        )
        self.toolbar.update()
        self.toolbar.pack(side="bottom", fill="x")

        self.canvas.draw_idle()
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
        path = Path(selected_file)
        extension = path.suffix.lower()

        if extension == ".txt" and path.stem.endswith("_scan_data"):
            figure, image, colorbar = spa.display_saved_raster_plot(path, channel=0)

            self.display_plot(
                figure=figure,
                axes=image.axes,
                source="saved_raster",
                metadata={
                    "data_file": path,
                    "channel": 0,
                    "image": image,
                    "colorbar": colorbar
                }
            )
            return

        if extension == ".png":
            stem = path.stem
            channel = 0

            if stem.endswith("_ch1"):
                base = stem.removesuffix("_ch1")
                channel = 1
            elif stem.endswith("_ch2"):
                base = stem.removesuffix("_ch2")
                channel = 2
            else:
                base = stem

            data_path = path.parent / f"{base}_scan_data.txt"

            if not data_path.exists():
                raise FileNotFoundError(f"Could not find raster data file: {data_path}")

            figure, image, colorbar = spa.display_saved_raster_plot(data_path, channel)

            self.display_plot(
                figure=figure,
                axes=image.axes,
                source="saved_raster",
                metadata={
                    "data_file": data_path,
                    "image_file": path,
                    "channel": channel,
                    "image": image,
                    "colorbar": colorbar
                }
            )
            return

        self.display_file(selected_file)