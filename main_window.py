"""Main-window layout and table-preview rendering."""
import tkinter as tk
from tkinter import ttk


class MainWindowMixin:
    def update_undo_button(self):
        if hasattr(self, "undo_button"):
            self.undo_button.configure(
                state="normal" if self.undo_stack else "disabled"
            )

    def build_interface(self):
        toolbar = ttk.Frame(self.root, padding=12)
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Открыть таблицу", command=self.open_file).pack(side="left")
        self.file_label = ttk.Label(toolbar, text="Файл не выбран")
        self.file_label.pack(side="left", padx=12)
        ttk.Button(toolbar, text="Настройки", command=self.open_settings).pack(side="right")

        actions = ttk.LabelFrame(self.root, text="Действия очистки", padding=10)
        actions.pack(fill="x", padx=12, pady=(0, 8))

        ttk.Checkbutton(
            actions, text="Удалить полностью пустые строки", variable=self.remove_empty_var
        ).grid(row=0, column=0, sticky="w", padx=(0, 18), pady=2)
        ttk.Checkbutton(
            actions, text="Удалить дубликаты строк", variable=self.remove_duplicates_var
        ).grid(row=0, column=1, sticky="w", padx=(0, 18), pady=2)
        ttk.Checkbutton(
            actions, text="Убрать пробелы по краям ячеек", variable=self.trim_spaces_var
        ).grid(row=1, column=0, sticky="w", padx=(0, 18), pady=2)

        buttons = ttk.Frame(actions)
        buttons.grid(row=0, column=2, rowspan=2, sticky="e", padx=(12, 0))
        self.undo_button = ttk.Button(
            buttons, text="Отменить изменения", command=self.undo_changes, state="disabled"
        )
        self.undo_button.pack(fill="x", pady=(0, 5))
        ttk.Button(buttons, text="Очистить данные", command=self.clean_data).pack(fill="x", pady=(0, 5))
        ttk.Button(buttons, text="Сохранить как…", command=self.save_as).pack(fill="x")
        actions.columnconfigure(2, weight=1)

        self.info_label = ttk.Label(
            self.root,
            text="Открой CSV или XLSX, выбери действия очистки и нажми «Очистить данные».",
            padding=(12, 0, 12, 8),
        )
        self.info_label.pack(anchor="w")

        table_frame = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, show="headings")
        vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Готов к работе")
        ttk.Label(
            self.root, textvariable=self.status_var, style="Status.TLabel",
            relief="sunken", anchor="w", padding=5,
        ).pack(fill="x", side="bottom")

    @staticmethod
    def display_value(value):
        if value is None:
            return ""
        return str(value)

    def display_table(self):
        self.tree.delete(*self.tree.get_children())
        column_count = len(self.headers)
        column_ids = [f"col_{index}" for index in range(column_count)]
        self.tree.configure(columns=column_ids)

        for index, column_id in enumerate(column_ids):
            header = self.headers[index]
            if header is None or str(header).strip() == "":
                header = f"Колонка {index + 1}"
            self.tree.heading(column_id, text=str(header))
            self.tree.column(column_id, width=150, minwidth=80, anchor="w")

        for row in self.rows[:self.preview_limit]:
            self.tree.insert("", "end", values=[self.display_value(value) for value in row])

        if len(self.rows) > self.preview_limit:
            self.status_var.set(
                f"Показаны первые {self.preview_limit} строк из {len(self.rows)}. Полные данные загружены."
            )

    def update_info(self):
        shown = min(len(self.rows), self.preview_limit)
        suffix = f"  |  В предпросмотре: {shown}" if len(self.rows) > self.preview_limit else ""
        self.info_label.configure(
            text=f"Строк с данными: {len(self.rows)}  |  Столбцов: {len(self.headers)}{suffix}"
        )
