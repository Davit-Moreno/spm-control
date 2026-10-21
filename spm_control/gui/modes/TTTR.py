from tkinter import messagebox

from spm_control.analysis import plotting
from spm_control.gui.modes import config, page_helpers
from spm_control.gui.layout import MAIN_LAYOUT
from spm_control.gui.modes.point_selector import PointSelector
from spm_control.managers.TTTR_manager import TTTRManager
from spm_control.managers.raster_manager import RasterManager


import spm_control.core_config as core_config


class TTTR_Page:
    def __init__(self, app):
        required_panels = {"mode_options", "option_parameters", "mode_display"}

        self.app = app
        self.panels = app.panels
        self.selected_xy = None
        self.Scan_Config = core_config.SCAN_CONFIG
        self.Hardware_Config = core_config.HARDWARE_CONFIG

        self.tttr_manager = TTTRManager(gui_root=app, hardware_manager=app.hardware_manager, time_manager=app.time_manager)
        self.raster_manager = RasterManager(app, app.hardware_manager, time_manager=app.time_manager)

        page_helpers.reload_panels(self.panels, MAIN_LAYOUT, required_panels, notMain=True)
        page_helpers.load_required_panels(self, self.panels, required_panels)

        self.point_selector = None
        self.entries = {}

        self.tttr_results = None
        self.plot_windows = []
        self.last_plots = []
        self.analysis_figure = None
        self.analysis_results = []

        self.OpenTTTRMenu()
        self.build_mode_ops()

    def begin_point_selection(self):
        if self.app.main_display.source not in ("live_raster", "saved_raster", "filtered_raster"):
            messagebox.showerror(
                "No Raster Scan",
                "Select Point needs a raster scan on the display. Open one from the Folder Menu first.",
                parent=self.app
            )
            return
        # Clicking any other plot, like an intensity trace, would send its time and counts to the stage as a position

        try:
            canvas, axes = self.app.main_display.get_active_plot()
        except RuntimeError as error:
            messagebox.showerror(
                "No Active Plot",
                str(error),
                parent=self.app
            )
            return

        if self.point_selector is not None:
            self.point_selector.cleanup()

        self.point_selector = PointSelector(
            canvas=canvas,
            axes=axes,
            callback=self.point_selected
        )

        self.point_selector.enable()

    def point_selected(self, point):
        try:
            x, y = map(float, point)
            self.selected_xy = (x, y)

            scan_settings = core_config.load_named_settings("scan", self.Scan_Config)
            position = {"x": x, "y": y, "z": float(scan_settings["z_focus"])}

            config.update_selection(position, "move", self.Scan_Config, nextCall=self.raster_manager.move_piezo)
            print(f"Selected TTTR point: ({x:.3f}, {y:.3f})")

        except Exception as error:
            page_helpers.throwError(str(error))

    def begin_measurement(self):
        if self.selected_xy is None:
            page_helpers.throwError("Please select a point before beginning the measurement.")
            return

        try:
            config.update(self.entries, "tttr", self.Scan_Config, emptyOk=True)
            self.tttr_manager.start()

        except Exception as error:
            page_helpers.throwError(str(error))

    def stop_measurement(self):
        try:
            self.tttr_manager.stop()
        except Exception as error:
            page_helpers.throwError(str(error))

    def mode_changed(self, mode):
        if mode == "T3":
            for frame in self.parameter_panel.t3_frames:
                frame.place()

            selected_mode = "t3"
        else:
            for frame in self.parameter_panel.t3_frames:
                frame.place_forget()

            selected_mode = "t2"

        config.update_selection({"default_mode": selected_mode}, "hydraharp", self.Hardware_Config)

    def OpenTTTRMenu(self):
        p = page_helpers.reload_panel(self.panels, MAIN_LAYOUT, "option_parameters")
        p.entries = self.entries

        p.title_frame = page_helpers.createFrame(p, "title_frame", [0, 0, 1, 0.1], outline=True)
        p.title_frame.pack_propagate(False)
        p.title = page_helpers.createLabel(p.title_frame, "TTTR Menu", sz=24, side="top", y_space=(4, 4))

        p.first_row = page_helpers.createFrame(p, "first_row", [0.1, 0.12, 0.7, 0.05])
        p.entries["acquisition_time"] = page_helpers.createSingleEntry(p.first_row, "Acquisition Time (s)", numbered_entry=True, placeholder="e.g. 1200")
        page_helpers.bind_entry(p.entries["acquisition_time"], min_val=0.001, max_val=36000)

        p.second_row = page_helpers.createFrame(p, "second_row", [0.1, 0.2, 0.5, 0.08])
        p.mode = page_helpers.createSelection(p.second_row, ["T2", "T3"], default="T2", command=self.mode_changed, spacing=6)

        p.sixth_row = page_helpers.createFrame(p, "sixth_row", [0.1, 0.28, 0.5, 0.06])
        p.entries["delay_min"] = page_helpers.createSingleEntry(p.sixth_row, "Delay Min (ps)", numbered_entry=True, placeholder="-1e5")

        p.seventh_row = page_helpers.createFrame(p, "seventh_row", [0.1, 0.34, 0.6, 0.06])
        p.entries["num_bins"] = page_helpers.createSingleEntry(p.seventh_row, "Number of Bins", numbered_entry=True, placeholder="100")

        p.eighth_row = page_helpers.createFrame(p, "eighth_row", [0.1, 0.4, 0.5, 0.06])
        p.entries["delay_max"] = page_helpers.createSingleEntry(p.eighth_row, "Delay Max (ps)", numbered_entry=True, placeholder="1e5")


        p.t3_frames = []

        p.t3_options = page_helpers.createFrame(p, "t3_options", [0.1, 0.52, 0.6, 0.08])
        p.entries["pulse_delay_min"] = page_helpers.createSingleEntry(p.t3_options, "Pulse Delay Min", numbered_entry=True, placeholder="-1.5")
        p.t3_frames.append(p.t3_options)

        p.t3_options_2 = page_helpers.createFrame(p, "t3_options_2", [0.1, 0.6, 0.6, 0.08])
        p.entries["pulse_num_bins"] = page_helpers.createSingleEntry(p.t3_options_2, "Number of Bins", numbered_entry=True, placeholder="0.3")
        p.t3_frames.append(p.t3_options_2)

        p.t3_options_3 = page_helpers.createFrame(p, "t3_options_3", [0.1, 0.68, 0.6, 0.08])
        p.entries["pulse_delay_max"] = page_helpers.createSingleEntry(p.t3_options_3, "Pulse Delay Max", numbered_entry=True, placeholder="1.5")
        p.t3_frames.append(p.t3_options_3)


        page_helpers.bind_entry(p.entries["delay_min"], nextE=p.entries["num_bins"], min_val=-1000000, max_val=1000000, ranged=True)
        page_helpers.bind_entry(p.entries["num_bins"], nextE=p.entries["delay_max"], min_val=0.001, max_val=1000000, ranged=True)
        page_helpers.bind_entry(p.entries["delay_max"], nextE=p.entries["pulse_delay_min"], min_val=-1000000, max_val=1000000, ranged=True)

        page_helpers.bind_entry(p.entries["pulse_delay_min"], nextE=p.entries["pulse_num_bins"], min_val=-1000, max_val=1000, ranged=True)
        page_helpers.bind_entry(p.entries["pulse_num_bins"], nextE=p.entries["pulse_delay_max"], min_val=0.001, max_val=1000, ranged=True)
        page_helpers.bind_entry(p.entries["pulse_delay_max"], min_val=-1000, max_val=1000, ranged=True)


        for frame in p.t3_frames:
            frame.place_forget()
        p.third_row = page_helpers.createFrame(p, "third_row", [0.0625, 0.9, 0.25, 0.05])
        p.select_point = page_helpers.createButton(p.third_row, "Select Point", 5, self.begin_point_selection)

        p.fourth_row = page_helpers.createFrame(p, "fourth_row", [0.375, 0.9, 0.25, 0.05])
        p.take_measurement = page_helpers.createButton(p.fourth_row, "Measure", 5, self.begin_measurement, color="green", hcolor="#14532D")

        p.fifth_row = page_helpers.createFrame(p, "fifth_row", [0.6875, 0.9, 0.25, 0.05])
        p.stop_measurement = page_helpers.createButton(p.fifth_row, "Stop", 5, self.stop_measurement, color="red", hcolor="#7F1D1D")

        self.parameter_panel = p
        self.mode_changed("T2")

    def OpenPlotterMenu(self):
        p = page_helpers.reload_panel(self.panels, MAIN_LAYOUT, "option_parameters")
        p.checkboxes = {}
        p.entries = {}

        p.title_frame = page_helpers.createFrame(p, "title_frame", [0, 0, 1, 0.1], outline=True)
        p.title_frame.pack_propagate(False)
        p.title = page_helpers.createLabel(p.title_frame, "TTTR Plotting Menu", sz=24, side="top", y_space=(4, 4))

        p.first_row = page_helpers.createFrame(p, "first_row", [0.1, 0.12, 0.6, 0.05])
        p.checkboxes["intensity"] = page_helpers.createCheckbox(
            p.first_row,
            "Intensity",
            lambda result_file, settings, title: plotting.create_intensity_plot(result_file, title=title)
        )

        p.g1_row = page_helpers.createFrame(p, "g1_row", [0.1, 0.19, 0.6, 0.05])
        p.checkboxes["g1"] = page_helpers.createCheckbox(
            p.g1_row,
            "g1 (trPL)",
            lambda result_file, settings, title: plotting.create_g1_plot(result_file, title=title)[0]
        )
        # Uses the same defaults as the G1 plotter test, the trPL Analysis menu has the fitting options

        p.second_row = page_helpers.createFrame(p, "second_row", [0.1, 0.26, 0.6, 0.05])
        p.checkboxes["g2"] = page_helpers.createCheckbox(
            p.second_row,
            "g2",
            lambda result_file, settings, title: plotting.create_g2_plot(
                result_file,
                float(settings["repetition_rate"]) * 1e6,
                title=title
            )
        )
        # Each checkbox keeps the function that makes its plot, run later by Plot for the checked boxes

        try:
            saved_rate = core_config.load_named_settings("tttr_plot", self.Scan_Config).get("repetition_rate", 1)
        except KeyError:
            saved_rate = 1

        p.third_row = page_helpers.createFrame(p, "third_row", [0.1, 0.36, 0.7, 0.05])
        p.entries["repetition_rate"] = page_helpers.createSingleEntry(p.third_row, "Rep Rate (MHz)", numbered_entry=True, placeholder=str(saved_rate))
        page_helpers.bind_entry(p.entries["repetition_rate"], min_val=0.001, max_val=1000)
        # The saved rate is shown as the placeholder, so leaving the box empty keeps it

        p.measurement_row = page_helpers.createFrame(p, "measurement_row", [0.05, 0.72, 0.9, 0.14])
        p.measurement_label = page_helpers.createLabel(p.measurement_row, "No measurement selected", sz=14, side="top", wraplength=230)

        p.fourth_row = page_helpers.createFrame(p, "fourth_row", [0.0625, 0.9, 0.25, 0.05])
        p.select_measurement = page_helpers.createButton(p.fourth_row, "Select", 5, self.select_measurement)

        p.fifth_row = page_helpers.createFrame(p, "fifth_row", [0.375, 0.9, 0.25, 0.05])
        p.plot = page_helpers.createButton(p.fifth_row, "Plot", 5, self.plot_measurement, color="green", hcolor="#14532D")

        p.sixth_row = page_helpers.createFrame(p, "sixth_row", [0.6875, 0.9, 0.25, 0.05])
        p.save = page_helpers.createButton(p.sixth_row, "Save", 5, self.save_tttr_plots)

        self.plotter_panel = p

        if self.tttr_results is not None:
            p.measurement_label.configure(text=self.tttr_results["measurement"].name)

    def select_measurement(self):
        selected_file = page_helpers.askForFile("Select Measurement", extension="ptu", allow_all=False)

        if selected_file is None:
            return

        results = plotting.find_tttr_results(selected_file)

        if results is None:
            page_helpers.throwError("Please select a .ptu file.")
            return

        self.tttr_results = results
        self.plotter_panel.measurement_label.configure(text=results["measurement"].name)

    def plot_measurement(self):
        if self.tttr_results is None:
            page_helpers.throwError("Please select a measurement first.")
            return

        if not any(checkbox.get() for checkbox in self.plotter_panel.checkboxes.values()):
            page_helpers.throwError("Please check at least one plot.")
            return

        try:
            config.update(self.plotter_panel.entries, "tttr_plot", self.Scan_Config, nextCall=self.create_tttr_plots, emptyOk=True)
        except Exception as error:
            page_helpers.throwError(str(error))

    def create_tttr_plots(self):
        settings = core_config.load_named_settings("tttr_plot", self.Scan_Config)
        name = self.tttr_results["measurement"].stem

        plots = []
        skipped = []

        for key, checkbox in self.plotter_panel.checkboxes.items():
            if not checkbox.get():
                continue

            result_file = self.tttr_results[key]

            if result_file is None:
                skipped.append(f"{key}: no {key} file found in this measurement's .run folders")
                continue

            try:
                plots.append((key, result_file, checkbox.delayed_command(result_file, settings, f"{key} · {name}")))
            except ValueError as error:
                skipped.append(f"{key}: {error}")
        # Missing or unreadable results are collected into one warning instead of stopping the other plots

        if skipped:
            page_helpers.throwWarning("Some plots were skipped:\n\n" + "\n".join(skipped))

        if plots:
            self.show_tttr_plots(plots)

    def show_tttr_plots(self, plots):
        for window in self.plot_windows:
            if window.winfo_exists():
                window.destroy()

        self.plot_windows = []
        self.last_plots = plots
        # Windows from the previous Plot are closed so they don't pile up, the new plots are kept for Save

        if len(plots) == 1:
            key, result_file, figure = plots[0]
            self.app.main_display.display_plot(figure, source="tttr_plot")
            self.app.file_display.set_path(result_file)
            return

        for offset, (key, result_file, figure) in enumerate(plots):
            title = f"{key} · {self.tttr_results['measurement'].stem}"
            self.plot_windows.append(page_helpers.popOutFigure(self.app, figure, title, offset=offset))
        # Several plots each open in their own window in front, leaving the raster on the main display


    def save_figures(self, saves):
        """
        Saves (figure, path) pairs, asking once before replacing files that already exist.
        A None figure means the path is the trPL fit results text file
        """
        existing = [path.name for figure, path in saves if path.exists()]

        def save():
            for figure, path in saves:
                if figure is None:
                    plotting.save_fit_results(self.analysis_results, path, self.tttr_results["g1"])
                else:
                    figure.savefig(path, dpi=300, bbox_inches="tight")

            folders = sorted({path.parent.name for figure, path in saves})
            messagebox.showinfo("Saved", "Saved " + ", ".join(path.name for figure, path in saves) + " in\n" + "\n".join(folders), parent=self.app)

        if existing:
            page_helpers.confirmation(f"{', '.join(existing)} already {'exists' if len(existing) == 1 else 'exist'}. Replace?", nextCall=save)
        else:
            save()

    def save_tttr_plots(self):
        if not self.last_plots:
            page_helpers.throwError("Please plot something first.")
            return

        self.save_figures([(figure, plotting.plot_save_path(result_file, key)) for key, result_file, figure in self.last_plots])
        # Each plot is saved next to its data with the old scripts' names, like g2plot.png in the .g2.run folder

    def OpenAnalysisMenu(self):
        p = page_helpers.reload_panel(self.panels, MAIN_LAYOUT, "option_parameters")
        p.fit_options = {}
        p.display_options = {}
        p.entries = {}

        p.title_frame = page_helpers.createFrame(p, "title_frame", [0, 0, 1, 0.1], outline=True)
        p.title_frame.pack_propagate(False)
        p.title = page_helpers.createLabel(p.title_frame, "trPL Analysis", sz=24, side="top", y_space=(4, 4))

        p.mono_row = page_helpers.createFrame(p, "mono_row", [0.05, 0.12, 0.42, 0.05])
        p.fit_options["mono"] = page_helpers.createCheckbox(p.mono_row, "Mono Fit", font_size=14)
        p.bi_row = page_helpers.createFrame(p, "bi_row", [0.53, 0.12, 0.42, 0.05])
        p.fit_options["bi"] = page_helpers.createCheckbox(p.bi_row, "Bi Fit", default=True, font_size=14)

        p.sum_row = page_helpers.createFrame(p, "sum_row", [0.05, 0.19, 0.42, 0.05])
        p.sum = page_helpers.createCheckbox(p.sum_row, "Sum SPADs", default=True, font_size=14)
        p.sum.configure(command=self.sum_toggled)
        # Runs as soon as Sum is clicked, unlike delayed_command which waits for a button

        p.channel_row = page_helpers.createFrame(p, "channel_row", [0.05, 0.26, 0.9, 0.06])
        p.channel = page_helpers.createSelection(p.channel_row, ["Ch. 0", "Ch. 1", "Both"], default="Both", spacing=6)

        p.normalize_row = page_helpers.createFrame(p, "normalize_row", [0.05, 0.34, 0.42, 0.05])
        p.display_options["normalize"] = page_helpers.createCheckbox(p.normalize_row, "Normalize", default=True, font_size=14)
        p.align_row = page_helpers.createFrame(p, "align_row", [0.53, 0.34, 0.42, 0.05])
        p.display_options["align_peak"] = page_helpers.createCheckbox(p.align_row, "Peak at 0", default=True, font_size=14)

        p.background_row = page_helpers.createFrame(p, "background_row", [0.05, 0.41, 0.42, 0.05])
        p.display_options["subtract_background"] = page_helpers.createCheckbox(p.background_row, "Background", default=True, font_size=14)
        p.residual_row = page_helpers.createFrame(p, "residual_row", [0.53, 0.41, 0.42, 0.05])
        p.display_options["residuals"] = page_helpers.createCheckbox(p.residual_row, "Residuals", font_size=14)

        p.from_row = page_helpers.createFrame(p, "from_row", [0.05, 0.48, 0.9, 0.06])
        p.from_label = page_helpers.createLabel(p.from_row, "From:", sz=14, side="left", x_space=(10, 0))
        p.background_from = page_helpers.createSelection(p.from_row, ["End", "Start"], default="End", spacing=6)
        # The end is after the decay has died out, the start is before the pulse arrives, both are only background

        p.points_row = page_helpers.createFrame(p, "points_row", [0.1, 0.56, 0.8, 0.05])
        p.entries["background_points"] = page_helpers.createSingleEntry(p.points_row, "Background Points", numbered_entry=True, placeholder="10")
        page_helpers.bind_entry(p.entries["background_points"], min_val=1, max_val=500, multi=1, emptyOk=True)

        p.start_row = page_helpers.createFrame(p, "start_row", [0.1, 0.63, 0.8, 0.05])
        p.entries["fit_start"] = page_helpers.createSingleEntry(p.start_row, "Fit Start (ns)", numbered_entry=True, placeholder="peak")
        page_helpers.bind_entry(p.entries["fit_start"], min_val=-1000, max_val=1000, emptyOk=True)

        p.end_row = page_helpers.createFrame(p, "end_row", [0.1, 0.7, 0.8, 0.05])
        p.entries["fit_end"] = page_helpers.createSingleEntry(p.end_row, "Fit End (ns)", numbered_entry=True, placeholder="end")
        page_helpers.bind_entry(p.entries["fit_end"], min_val=-1000, max_val=1000, emptyOk=True)
        # Empty boxes mean the defaults shown in grey, times are read off the plot's x-axis

        p.measurement_row = page_helpers.createFrame(p, "measurement_row", [0.05, 0.77, 0.9, 0.11])
        p.measurement_label = page_helpers.createLabel(p.measurement_row, "Select a measurement in the Plotting Menu", sz=14, side="top", wraplength=230)

        if self.tttr_results is not None:
            p.measurement_label.configure(text=self.tttr_results["measurement"].name)

        p.update_row = page_helpers.createFrame(p, "update_row", [0.0625, 0.9, 0.4, 0.05])
        p.update = page_helpers.createButton(p.update_row, "Update", 5, self.update_analysis, color="green", hcolor="#14532D")

        p.save_row = page_helpers.createFrame(p, "save_row", [0.5375, 0.9, 0.4, 0.05])
        p.save = page_helpers.createButton(p.save_row, "Save", 5, self.save_analysis)

        self.analysis_panel = p
        self.sum_toggled()
        # Sum starts checked, so the channel options start hidden

    def sum_toggled(self):
        p = self.analysis_panel

        if p.sum.get():
            p.channel_row.place_forget()
        else:
            page_helpers.showFrame(p.channel_row)
        # The channel choice only matters when the SPADs aren't summed

    def read_number(self, entry, default=None):
        raw_value = entry.get().strip()
        return default if raw_value == "" else float(raw_value)

    def update_analysis(self):
        if self.tttr_results is None or self.tttr_results["g1"] is None:
            page_helpers.throwError("Please select a measurement with trPL (g1) results in the Plotting Menu first.")
            return

        p = self.analysis_panel

        try:
            background_points = int(self.read_number(p.entries["background_points"], default=10))
            fit_start = self.read_number(p.entries["fit_start"])
            fit_end = self.read_number(p.entries["fit_end"])
        except ValueError:
            page_helpers.throwError("Background Points, Fit Start and Fit End must be numbers.")
            return

        if p.sum.get():
            channels = (0, 1)
            fit_channels = ("sum",)
        else:
            channels = {"Ch. 0": (0,), "Ch. 1": (1,), "Both": (0, 1)}[p.channel.get()]
            fit_channels = None
        # With Sum, Ch. 0 and Ch. 1 are drawn in blue and red and only their sum is fitted, as one black line
        fits = [model for model, checkbox in p.fit_options.items() if checkbox.get()]
        options = {name: checkbox.get() for name, checkbox in p.display_options.items()}

        try:
            figure, results = plotting.create_g1_plot(
                self.tttr_results["g1"],
                title=f"trPL · {self.tttr_results['measurement'].stem}",
                channels=channels,
                fits=fits,
                fit_channels=fit_channels,
                fit_start=fit_start,
                fit_end=fit_end,
                background_points=background_points,
                background_from=p.background_from.get().lower(),
                **options
            )
        except ValueError as error:
            page_helpers.throwError(str(error))
            return

        self.analysis_figure = figure
        self.analysis_results = results

        self.app.main_display.display_plot(figure, axes=figure.axes[0], source="tttr_plot")
        self.app.file_display.set_path(self.tttr_results["g1"])

        failed = [f"{plotting.channel_name(result['channel'])} {result['model']}: {result['error']}" for result in results if "error" in result]

        if failed:
            page_helpers.throwWarning("Some fits failed:\n\n" + "\n".join(failed))

    def save_analysis(self):
        if self.analysis_figure is None:
            page_helpers.throwError("Please click Update first.")
            return

        plot_path = plotting.plot_save_path(self.tttr_results["g1"], "g1")
        saves = [(self.analysis_figure, plot_path)]

        if self.analysis_results:
            saves.append((None, plot_path.with_name("trplfit.txt")))
        # trplplot.png and trplfit.txt go in the .g1.run folder next to the g1 data

        self.save_figures(saves)

    def build_mode_ops(self):
        options_loadout = {"select_point": self.OpenTTTRMenu, "g2_plot": self.OpenPlotterMenu, "trPL": self.OpenAnalysisMenu}
        page_helpers.createToolbar(self.mode_options, options_loadout, 0.08)

    def cleanup(self):
        if self.point_selector is not None:
            self.point_selector.cleanup()
            self.point_selector = None