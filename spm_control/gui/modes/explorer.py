from spm_control.gui.modes import page_helpers
from spm_control.gui.layout import MAIN_LAYOUT
from spm_control.scan import scan_plot_and_analysis as spa


class Explorer_Page:
    def __init__(self, app):
        required_panels = {
            "mode_options",
            "mode_display",
            "option_parameters",
        }

        self.app = app
        self.panels = app.panels

        page_helpers.reload_panels(
            self.panels,
            MAIN_LAYOUT,
            required_panels,
            notMain=True
        )

        page_helpers.load_required_panels(
            self,
            self.panels,
            required_panels
        )

        self.OpenFolderMenu()

    def OpenFolderMenu(self):
        p = page_helpers.reload_panel(
            self.panels,
            MAIN_LAYOUT,
            "option_parameters"
        )

        p.entries = {}

        p.title_frame = page_helpers.createFrame(
            p,
            "title_frame",
            [0, 0, 1, 0.1],
            outline=True
        )
        p.title_frame.pack_propagate(False)

        p.title = page_helpers.createLabel(
            p.title_frame,
            "Folder Menu",
            sz=24,
            side="top",
            y_space=(4, 4)
        )

        p.first_row = page_helpers.createFrame(
            p,
            "first_row",
            [0.1, 0.12, 0.7, 0.05]
        )
        p.entries["filter_name"] = page_helpers.createSingleEntry(
            p.first_row,
            "Filter",
            numbered_entry=False,
            placeholder="e.g. g2"
        )

        p.second_row = page_helpers.createFrame(
            p,
            "second_row",
            [0.1, 0.19, 0.7, 0.05]
        )
        p.entries["extension"] = page_helpers.createSingleEntry(
            p.second_row,
            "Extension",
            numbered_entry=False,
            placeholder="e.g. txt"
        )

        page_helpers.bind_entry(
            p.entries["filter_name"],
            min_val=None,
            max_val=None
        )

        page_helpers.bind_entry(
            p.entries["extension"],
            min_val=None,
            max_val=None
        )

        p.last_row = page_helpers.createFrame(
            p,
            "third_row",
            [0.35, 0.9, 0.3, 0.05]
        )

        p.select_file = page_helpers.createButton(
            p.last_row,
            "Select File",
            5,
            self.select_and_display_file
        )

        p.compare_row = None
        self.update_compare_button()

    def select_and_display_file(self):
        p = self.panels["option_parameters"]

        selected_file = page_helpers.askForFile(
            "Open File",
            extension=p.entries["extension"].get(),
            name_filter=p.entries["filter_name"].get()
        )

        if selected_file is None:
            return

        try:
            self.app.main_display.display_selected_file(selected_file)
            self.app.file_display.set_path(selected_file)
            print("Selected file:", selected_file)

        except Exception as error:
            page_helpers.throwError(str(error))

        self.update_compare_button()

    def update_compare_button(self):
        """
        Shows the Compare button only while a raster scan occupies the display
        """
        p = self.panels["option_parameters"]

        if p.compare_row is not None:
            p.compare_row.destroy()
            p.compare_row = None

        if not self.current_file_is_scan():
            return

        p.compare_row = page_helpers.createFrame(
            p,
            "compare_row",
            [0.35, 0.83, 0.3, 0.05]
        )

        p.compare = page_helpers.createButton(
            p.compare_row,
            "Compare with...",
            5,
            self.select_and_compare_files
        )

    def current_file_is_scan(self):
        if self.app.hardware_manager.get_operation() == "raster_scan":
            return False
        # While scanning, the live plot is shown but the path bar still holds the previous file

        current_file = page_helpers.get_file(self.app.file_display)

        if not current_file:
            return False

        scan = spa.find_scan_data(current_file)
        return scan is not None and scan[0].exists()

    def select_and_compare_files(self):
        p = self.panels["option_parameters"]

        left_file = page_helpers.get_file(self.app.file_display)
        right_file = page_helpers.askForFile(
            "Pick file to compare",
            extension=p.entries["extension"].get(),
            name_filter=p.entries["filter_name"].get()
        )

        if right_file is None:
            return

        try:
            self.app.main_display.display_side_by_side(left_file, right_file)
            self.app.file_display.set_secondary_path(right_file)
            print("Comparing:", left_file, "with", right_file)

        except Exception as error:
            page_helpers.throwError(str(error))