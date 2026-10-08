from pathlib import Path
import customtkinter as ctk
from PIL import Image
from spm_control.gui.modes import validators as check
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk



# NOTE MOST IF NOT ALL THESE WIDGETS EITHER SCALE TO PARENT FRAME OR FILL UP FRAME ENTIRELY
# SMALLER WIDGETS LIKE BUTTONS AND TEXT ESPECIALLY FILL UP FRAME

def createPanels(parent, layout):
    """
    Looks at the name and dimensions in the layout file and creates panels accordingly
    """
    panels = {}
    for name, dims in layout.items():
        panels[name] = create_panel(parent, name, dims)
    return panels


def create_panel(parent, name, dims):
    """
    Creating frame panel with relative dimensional coordinates to parent
    """
    x, y, w, h = dims

    panel = ctk.CTkFrame(
        parent,
        border_width=2,
        border_color="white",
        fg_color="black",
        )
    
    panel.place(
        relx=x,
        rely=y,
        relwidth=w,
        relheight=h,
    )

    return panel


def reload_panel(panels, layout, panel_name):
    """
    Destroys the panel and recreates the panel
    """
    old_panel = panels[panel_name]
    parent = old_panel.master
    old_panel.destroy()

    new_panel = create_panel(parent, panel_name,layout[panel_name])
    panels[panel_name] = new_panel

    return new_panel


def reload_panels(panels, layout, panel_names, notMain = False):
    """
    Destroy and recreate multiple panels.
    """
    if (notMain == True):
        panel_names.remove("mode_display")
    for panel_name in panel_names:
        reload_panel(panels, layout, panel_name)

    return panels

def load_required_panels(page, panels, required_panels):
    """
    Loads the required panels out of provided panels onto the page
    """
    page.panels = panels
    
    for name in required_panels: 
        if name not in panels:
            raise KeyError(f"Required panel '{name}' was not found in app.panels")

        setattr(page, name, panels[name])

def createFrame(parent, name, dimensions, outline = False):
    """
    Creates frame within parent frame (typically panel), with relative diemnsions and name
    """
    debug = False
    if not hasattr(parent, "frames"):
        parent.frames = {}

    if (debug == True):
            col1 ="black"
            col2 = "white"
    else:
        col1 = "transparent"
        col2 = ""

    if (outline == True):
        col1 ="black"
        col2 = "white"

    frame = ctk.CTkFrame(
        parent,
        border_width = 2,
        border_color = col2,
        fg_color = col1,
    )
    # Using relative coordinates because those scale
    frame.place(
        relx=dimensions[0],
        rely=dimensions[1],
        relwidth=dimensions[2],
        relheight=dimensions[3],
    )

    parent.frames[name] = frame
    return frame

def createToolbar(parent, loadout, button_size, horizontal=True):
    """
    Creates a toolbar of buttons of specified size horizontally or vertically,
    with png names as keys that also refer to assets folder and commands within
    the dictionary loadouts 
    """
    parent.options = {}
    assets = Path(__file__).resolve().parent.parent / "assets"

    for i, (name, command) in enumerate(loadout.items()):
        if (horizontal):
            dims = [button_size * i, 0, button_size, 1]
        else:
            dims = [0, button_size * i, 1, button_size]

        frame = createFrame(
            parent,
            f"{name}_frame",
            dims,
            outline=True,
        )

        button = createButtonDisplay(
            frame,
            str(assets / f"{name}.png"),
            command,
        )

        parent.options[name] = {
            "frame": frame,
            "button": button,
        }

def createButton(parent, name, cRad, func, color=None, hcolor=None):
    """Creates a regular text button that executes some function when clicked"""
    kwargs = {}

    if color is not None:
        kwargs["fg_color"] = color

    if hcolor is not None:
        kwargs["hover_color"] = hcolor

    button = ctk.CTkButton(
        master=parent,
        text=name,
        command=func,
        corner_radius=cRad,
        **kwargs
    )

    button.pack(fill="both", expand=True)
    return button


def createButtonDisplay(parent, PNG, func):
    """Creates a button display with an image"""
    raw_image = Image.open(PNG).convert("RGBA")

    my_button = ctk.CTkButton(
        master=parent,
        text="",
        command=func,
        fg_color="white",
        hover_color="gray"
    )

    my_button.pack(
        padx=10,
        pady=10,
        fill="both",
        expand=True
    )

    def resize_to_parent(event):
        available_width = event.width
        available_height = event.height

        image_width = int(available_width * 0.6)
        image_height = int(available_height * 0.6)

        btn_image = ctk.CTkImage(
            light_image=raw_image,
            dark_image=raw_image,
            size=(image_width, image_height)
        )

        my_button.configure(image=btn_image)
        my_button.image_ref = btn_image

    parent.bind("<Configure>", resize_to_parent)

    return my_button

def createCheckbox(
    parent,
    text,
    command=None,
    default=False,
    font_size=18,
    padx=10
):
    """Creates a checkbox with a label and a command that can be executed
    at a later time, because the command is stored as a custom variable
    within the checkbox object"""

    variable = ctk.BooleanVar(value=default)

    label = ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=font_size),
        anchor="w"
    )
    label.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(padx, 5)
    )

    checkbox = ctk.CTkCheckBox(
        parent,
        text="",
        variable=variable,
        onvalue=True,
        offvalue=False,
        width=24
    )
    checkbox.pack(
        side="right",
        padx=(5, padx)
    )

    checkbox.delayed_command = command

    return checkbox

def createRangeInput(parent, name, placeholder_min="min", placeholder_max="max"):
    """Creates a ranged input with a label and two entry fields for min and max values
    with validation to check of a typed character is a valid numerical entry"""
    # Could maybe use createSingleEntry call
    name = name.rstrip(":")
    vcmd = (parent.register(check.validate_numeric_typing), "%P", name)

    label = createLabel(
        parent,
        text=f"{name}:",
        sz=17,
        font="Arial",
        width=28,
        anchor="e",
        pack=False
    )

    label.pack(side="left", padx=(0, 5), pady=0)

    min_entry = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder_min,
        placeholder_text_color="#b0b0b0",
        width=52,
        height=26,
        font=("Arial", 14),
        justify="center",
        validate="key",
        validatecommand=vcmd
    )
    
    max_entry = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder_max,
        placeholder_text_color="#b0b0b0",
        width=52,
        height=26,
        font=("Arial", 14),
        justify="center",
        validate="key",
        validatecommand=vcmd
    )

    min_entry.pack(side="left", padx=(0, 6), pady=0)
    max_entry.pack(side="left", pady=0)

    return min_entry, max_entry

def createSingleEntry(
    parent,
    name,
    placeholder="value",
    label_width=28,
    entry_width=82,
    min_val=None,
    max_val=None,
    config_key=None,
    multi = 0,
    numbered_entry = True,
):
    # Config_key might be unecessary?
    """Creates a single entry field with optional parameters like:
    a minimum and maximum value, a configuration key, and ensuring
    that an entry is rounded to a valid multiple"""
    name = name.rstrip(":")
    config_key = config_key or name

    if numbered_entry:
        vcmd = (parent.register(check.validate_numeric_typing), "%P", name)
    else:
        vcmd = (parent.register(check.validate_typing), "%P", name)

    label = createLabel(
        parent,
        text=f"{name}:",
        sz=17,
        font="Arial",
        width=label_width,
        anchor="e",
        pack=False,
    )
    label.pack(side="left", padx=(0, 5), pady=0)

    entry = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        placeholder_text_color="#b0b0b0",
        width=entry_width,
        height=26,
        font=("Arial", 14),
        justify="center",
        validate="key",
        validatecommand=vcmd,
    )
    entry.pack(side="left", pady=0)

    return entry

def createLabel(
    parent,
    text="",
    sz=18,
    font="Arial",
    side="left",
    x_space=(10, 10),
    y_space=(0, 0),
    expand=False,
    pack=True,
    **kwargs
):
    """Creates a label"""
    label = ctk.CTkLabel(
        parent,
        text=text,
        font=(font, sz),
        **kwargs
    )

    if pack:
        label.pack(
            side=side,
            padx=x_space,
            pady=y_space,
            expand=expand
        )

    return label

def bind_entry(
    entry,
    nextE=None,
    min_val=0,
    max_val=100,
    multi=0,
    ranged=False,
    emptyOk=False
):
    """
    Binds entry ensuring minimum value and maximum value are correct
    Also checks for multiples, and if something is ranged or allowed to be empty.
    It can focus onto the next entry box (if) provided when enter key is pressed
    """
    if min_val is not None or max_val is not None:
        entry.bind(
            "<FocusOut>",
            lambda event: check.within_range(
                entry,
                min_val,
                max_val,
                multiple=multi,
                ranged_input=ranged,
                EnterKey=False,
                emptyOk=emptyOk
            )
        )

        entry.bind(
            "<Return>",
            lambda event: check.within_range(
                entry,
                min_val,
                max_val,
                multiple=multi,
                ranged_input=ranged,
                next_entry=nextE,
                EnterKey=True,
                emptyOk=emptyOk
            )
        )
    else:
        entry.bind(
            "<Return>",
            lambda event: check.within_range(
                entry,
                min_val,
                max_val,
                multiple=multi,
                next_entry=nextE,
                EnterKey=True,
                emptyOk=emptyOk
            )
        )

def get_file(file_display):
    """
    Gets the file display path
    which is useful for other pages
    """
    return file_display.get_path()

def askForFile(title, extension="", name_filter=""):
    """
    Opens a file picker limited to an extension if one is given,
    and only accepts files whose name contains name_filter.
    Returns None if nothing valid was picked
    """
    extension = extension.strip().lstrip(".")
    name_filter = name_filter.strip()

    if extension:
        filetypes = [
            (f"{extension.upper()} files", f"*.{extension}"),
            ("All files", "*.*")
        ]
    else:
        filetypes = [("All files", "*.*")]

    selected_file = filedialog.askopenfilename(
        title=title,
        filetypes=filetypes
    )

    if not selected_file:
        return None

    file_name = Path(selected_file).name

    if (
        name_filter
        and name_filter.casefold() not in file_name.casefold()
    ):
        throwError(f"Selected file does not contain '{name_filter}'.")
        return None

    return selected_file

def throwError(message):
    messagebox.showerror("Error", message)

def displayImage(frame, image_source):
    for widget in frame.winfo_children():
        widget.destroy()

    original = Image.open(image_source) if isinstance(image_source, (str, Path)) else image_source.copy()

    label = ctk.CTkLabel(frame, text="")
    label.pack(fill="both", expand=True)

    def resize(event):
        if event.width <= 1 or event.height <= 1:
            return

        image = original.copy()
        image.thumbnail((event.width, event.height))

        ctk_image = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=image.size
        )

        label.configure(image=ctk_image)
        label.image = ctk_image

    frame.bind("<Configure>", resize)
    frame.after_idle(lambda: resize(
        type("Event", (), {
            "width": frame.winfo_width(),
            "height": frame.winfo_height()
        })()
    ))

    return label

def createDisplayEntry(parent, name, value="0", label_width=80, entry_width=145, color = "#40E0D0"):
    value_var = ctk.StringVar(value=value)

    label = createLabel(
        parent,
        text=f"{name}:",
        sz=20,
        font="Arial",
        width=label_width,
        anchor="e",
        pack=False
    )
    label.pack(side="left", padx=(0, 8))

    entry = ctk.CTkEntry(
        parent,
        textvariable=value_var,
        width=entry_width,
        height=45,
        font=("Arial", 20, "bold"),
        text_color=color,
        justify="center",
        state="disabled"
    )
    entry.pack(side="left")

    return entry, value_var


def embedFigure(parent, figure):
    """
    Embeds a Matplotlib figure with its zoom/pan toolbar so it fills the parent frame
    """
    toolbar_frame = ctk.CTkFrame(parent, fg_color="transparent")
    toolbar_frame.pack(side="bottom", fill="x")

    canvas_frame = ctk.CTkFrame(parent, fg_color="transparent")
    canvas_frame.pack(side="top", fill="both", expand=True)

    canvas = FigureCanvasTkAgg(figure, master=canvas_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    toolbar = NavigationToolbar2Tk(
        canvas,
        toolbar_frame,
        pack_toolbar=False
    )
    toolbar.update()
    toolbar.pack(side="bottom", fill="x")

    canvas.draw_idle()
    return canvas

def confirmation(msg, T = "Confirm",nextCall = None):
    """
    Gives a confirmation popup with confirmation and a msg,
    if confirmed next call executes
    """
    confirmed = messagebox.askyesno(title=T, message=msg)

    if confirmed and nextCall is not None:
        nextCall()
    else:
        return

def createSelection(
    parent,
    texts,
    default=None,
    command=None,
    spacing=10,
    edge_padding=12,
    bg_color="#2b2b2b"
):
    """
    Creates a selection of two options, and command executes
    """
    if not texts:
        raise ValueError("texts must contain at least one option")

    selected = ctk.StringVar(value=default or texts[0])

    container = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=6)
    container.pack(fill="both", expand=True)

    row = ctk.CTkFrame(container, fg_color="transparent")
    row.pack(fill="both", expand=True, padx=edge_padding, pady=4)

    def changed():
        if command:
            command(selected.get())

    for i, text in enumerate(texts):
        radio = ctk.CTkRadioButton(
            row,
            text=text,
            value=text,
            variable=selected,
            command=changed,
            font=ctk.CTkFont(size=15),
            radiobutton_width=22,
            radiobutton_height=22,
            border_width_checked=5,
            border_width_unchecked=3
        )

        radio.pack(
            side="left",
            padx=(0, spacing) if i < len(texts) - 1 else 0,
            pady=2
        )

    return selected