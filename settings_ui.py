"""Settings dialog and theme management UI for TableCleaner."""
import tkinter as tk
from tkinter import messagebox, ttk


class SettingsUIMixin:
    def check_system_theme(self):
        if self.theme_mode == "system":
            detected = self.detect_windows_theme()
            if detected != self.current_theme:
                self.current_theme = detected
                self.apply_theme()
                self.status_var.set("Оформление обновлено по настройкам Windows.")
        try:
            self.root.after(5000, self.check_system_theme)
        except tk.TclError:
            pass

    def open_settings(self):
        if self.settings_window is not None:
            try:
                if self.settings_window.winfo_exists():
                    self.settings_window.lift()
                    self.settings_window.focus_force()
                    return
            except tk.TclError:
                self.settings_window = None

        window = tk.Toplevel(self.root)
        self.settings_window = window
        window.title("Настройки TableCleaner")
        window.geometry("480x540")
        window.minsize(440, 500)
        window.transient(self.root)
        window.protocol("WM_DELETE_WINDOW", lambda: self.close_settings_window(window))

        container = ttk.Frame(window, padding=16)
        container.pack(fill="both", expand=True)

        appearance = ttk.LabelFrame(container, text="Внешний вид", padding=10)
        appearance.pack(fill="x", pady=(0, 10))
        ttk.Label(appearance, text="Тема приложения:").grid(row=0, column=0, sticky="w", pady=4)
        theme_labels = {
            "Автоматически (как в Windows)": "system",
            "Светлая": "light",
            "Тёмная": "dark",
        }
        theme_reverse = {value: key for key, value in theme_labels.items()}
        theme_var = tk.StringVar(value=theme_reverse[self.theme_mode])
        theme_combo = ttk.Combobox(
            appearance, textvariable=theme_var, state="readonly", width=28,
            values=list(theme_labels.keys()),
        )
        theme_combo.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=4)
        ttk.Label(
            appearance,
            text="В автоматическом режиме тема следует настройке приложений Windows.",
            wraplength=390,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        appearance.columnconfigure(1, weight=1)

        preview = ttk.LabelFrame(container, text="Таблица", padding=10)
        preview.pack(fill="x", pady=(0, 10))
        ttk.Label(preview, text="Строк в предпросмотре:").grid(row=0, column=0, sticky="w")
        preview_var = tk.StringVar(value=str(self.preview_limit))
        ttk.Combobox(
            preview, textvariable=preview_var, state="readonly", width=12,
            values=("50", "100", "250", "500"),
        ).grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Label(
            preview, text="Остальные строки остаются загруженными и попадут в сохранённый файл.",
            wraplength=390,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        behavior = ttk.LabelFrame(container, text="Поведение программы", padding=10)
        behavior.pack(fill="x", pady=(0, 10))
        confirm_var = tk.BooleanVar(value=self.settings["confirm_before_clean"])
        summary_var = tk.BooleanVar(value=self.settings["show_operation_summary"])
        ttk.Checkbutton(
            behavior, text="Спрашивать подтверждение перед очисткой", variable=confirm_var,
        ).pack(anchor="w", pady=2)
        ttk.Checkbutton(
            behavior, text="Показывать окно с итогами очистки", variable=summary_var,
        ).pack(anchor="w", pady=2)

        defaults = ttk.LabelFrame(container, text="Операции, включённые по умолчанию", padding=10)
        defaults.pack(fill="x", pady=(0, 10))
        empty_var = tk.BooleanVar(value=self.settings["default_remove_empty"])
        duplicate_var = tk.BooleanVar(value=self.settings["default_remove_duplicates"])
        trim_var = tk.BooleanVar(value=self.settings["default_trim_spaces"])
        ttk.Checkbutton(defaults, text="Удалять пустые строки", variable=empty_var).pack(anchor="w", pady=1)
        ttk.Checkbutton(defaults, text="Удалять дубликаты строк", variable=duplicate_var).pack(anchor="w", pady=1)
        ttk.Checkbutton(defaults, text="Убирать пробелы по краям ячеек", variable=trim_var).pack(anchor="w", pady=1)

        footer = ttk.Frame(container)
        footer.pack(fill="x", side="bottom", pady=(6, 0))
        ttk.Button(
            footer, text="По умолчанию",
            command=lambda: self.reset_settings_dialog(
                theme_var, preview_var, confirm_var, summary_var,
                empty_var, duplicate_var, trim_var,
            ),
        ).pack(side="left")
        ttk.Button(
            footer, text="Отмена", command=lambda: self.close_settings_window(window)
        ).pack(side="right", padx=(6, 0))
        ttk.Button(
            footer, text="Применить",
            command=lambda: self.apply_settings_from_dialog(
                window, theme_var, theme_labels, preview_var, confirm_var, summary_var,
                empty_var, duplicate_var, trim_var,
            ),
        ).pack(side="right")

        window.grab_set()
        self.apply_theme()

    def close_settings_window(self, window):
        try:
            window.destroy()
        except tk.TclError:
            pass
        if self.settings_window is window:
            self.settings_window = None

    def reset_settings_dialog(
        self, theme_var, preview_var, confirm_var, summary_var,
        empty_var, duplicate_var, trim_var,
    ):
        theme_var.set("Автоматически (как в Windows)")
        preview_var.set("100")
        confirm_var.set(True)
        summary_var.set(True)
        empty_var.set(True)
        duplicate_var.set(True)
        trim_var.set(True)

    def apply_settings_from_dialog(
        self, window, theme_var, theme_labels, preview_var, confirm_var, summary_var,
        empty_var, duplicate_var, trim_var,
    ):
        try:
            new_preview = int(preview_var.get())
            if new_preview not in {50, 100, 250, 500}:
                raise ValueError
        except ValueError:
            messagebox.showerror("Некорректное значение", "Выбери количество строк из списка.", parent=window)
            return

        self.theme_mode = theme_labels.get(theme_var.get(), "system")
        self.settings.update({
            "theme_mode": self.theme_mode,
            "preview_rows": new_preview,
            "confirm_before_clean": bool(confirm_var.get()),
            "show_operation_summary": bool(summary_var.get()),
            "default_remove_empty": bool(empty_var.get()),
            "default_remove_duplicates": bool(duplicate_var.get()),
            "default_trim_spaces": bool(trim_var.get()),
        })
        self.preview_limit = new_preview
        self.remove_empty_var.set(self.settings["default_remove_empty"])
        self.remove_duplicates_var.set(self.settings["default_remove_duplicates"])
        self.trim_spaces_var.set(self.settings["default_trim_spaces"])
        self.current_theme = self.resolve_theme()
        self.apply_theme()
        self.display_table()
        self.update_info()
        self.save_settings()
        self.status_var.set("Настройки сохранены.")
        window.destroy()
        self.settings_window = None

    def apply_theme(self):
        palettes = {
            "light": {
                "bg": "#F3F5F8", "surface": "#FFFFFF", "field": "#FFFFFF",
                "fg": "#202733", "muted": "#5F6B7A", "button": "#E7ECF2",
                "button_active": "#D8E1EC", "border": "#CCD4DF",
                "heading": "#E8EDF3", "accent": "#C6DDFB", "selected_fg": "#17243A",
            },
            "dark": {
                "bg": "#181D26", "surface": "#222936", "field": "#1D2430",
                "fg": "#E8EDF5", "muted": "#B1BDCD", "button": "#343E4E",
                "button_active": "#43516A", "border": "#414C5D",
                "heading": "#2B3442", "accent": "#365B88", "selected_fg": "#FFFFFF",
            },
        }
        colors = palettes.get(self.current_theme, palettes["light"])
        self.root.configure(background=colors["bg"])
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        self.style.configure(
            "TLabelframe", background=colors["bg"], foreground=colors["fg"],
            bordercolor=colors["border"],
        )
        self.style.configure(
            "TLabelframe.Label", background=colors["bg"], foreground=colors["fg"]
        )
        self.style.configure(
            "TButton", background=colors["button"], foreground=colors["fg"],
            bordercolor=colors["border"], padding=(10, 6), relief="flat",
        )
        self.style.map(
            "TButton",
            background=[("disabled", colors["surface"]), ("pressed", colors["button_active"]),
                        ("active", colors["button_active"])],
            foreground=[("disabled", colors["muted"])],
        )
        self.style.configure(
            "TCheckbutton", background=colors["bg"], foreground=colors["fg"], padding=3
        )
        self.style.map(
            "TCheckbutton",
            background=[("active", colors["bg"])],
            foreground=[("disabled", colors["muted"])],
        )
        self.style.configure(
            "Treeview", background=colors["field"], fieldbackground=colors["field"],
            foreground=colors["fg"], rowheight=27, bordercolor=colors["border"],
            lightcolor=colors["border"], darkcolor=colors["border"],
        )
        self.style.map(
            "Treeview",
            background=[("selected", colors["accent"])],
            foreground=[("selected", colors["selected_fg"])],
        )
        self.style.configure(
            "Treeview.Heading", background=colors["heading"], foreground=colors["fg"],
            bordercolor=colors["border"], padding=7, relief="flat",
        )
        self.style.map(
            "Treeview.Heading", background=[("active", colors["button_active"])],
        )
        self.style.configure(
            "Vertical.TScrollbar", background=colors["button"],
            troughcolor=colors["bg"], bordercolor=colors["border"],
        )
        self.style.configure(
            "Horizontal.TScrollbar", background=colors["button"],
            troughcolor=colors["bg"], bordercolor=colors["border"],
        )
        self.style.configure(
            "Status.TLabel", background=colors["surface"], foreground=colors["muted"],
            padding=5,
        )
        if self.settings_window is not None:
            try:
                if self.settings_window.winfo_exists():
                    self.settings_window.configure(background=colors["bg"])
            except tk.TclError:
                pass
