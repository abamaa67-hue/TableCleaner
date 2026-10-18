"""CSV/XLSX file operations, data cleaning, undo, and export."""
import csv
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from openpyxl import Workbook, load_workbook


class DataOperationsMixin:
    def open_file(self):
        filename = filedialog.askopenfilename(
            title="Выбери таблицу",
            filetypes=[
                ("Таблицы CSV и Excel", "*.csv *.xlsx"),
                ("CSV", "*.csv"),
                ("Excel", "*.xlsx"),
            ],
        )
        if not filename:
            return

        path = Path(filename)
        try:
            if path.suffix.lower() == ".csv":
                raw_data = self.read_csv(path)
            elif path.suffix.lower() == ".xlsx":
                raw_data = self.read_excel(path)
            else:
                messagebox.showerror("Неподдерживаемый формат", "Выбери файл CSV или XLSX.")
                return

            if not raw_data:
                messagebox.showwarning("Пустой файл", "В выбранном файле нет данных.")
                return

            column_count = max((len(row) for row in raw_data), default=0)
            if column_count == 0:
                messagebox.showwarning("Пустой файл", "В выбранном файле нет столбцов.")
                return

            self.headers = list(raw_data[0]) + [None] * (column_count - len(raw_data[0]))
            self.rows = [list(row) + [None] * (column_count - len(row)) for row in raw_data[1:]]
            self.source_path = path
            # Undo history belongs to the currently opened file only.
            self.undo_stack.clear()
            self.removed_empty = 0
            self.removed_duplicates = 0
            self.trimmed_cells = 0
            self.update_undo_button()
            self.display_table()
            self.file_label.configure(text=path.name)
            self.update_info()
            self.status_var.set(f"Загружен файл: {path.name}")
        except Exception as error:
            messagebox.showerror("Ошибка при открытии", f"Не удалось прочитать файл:\n\n{error}")

    @staticmethod
    def read_csv(path: Path):
        last_error = None
        for encoding in ("utf-8-sig", "cp1251", "latin-1"):
            try:
                with path.open("r", encoding=encoding, newline="") as file:
                    sample = file.read(8192)
                    file.seek(0)
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                    except csv.Error:
                        dialect = csv.excel
                    return list(csv.reader(file, dialect))
            except UnicodeDecodeError as error:
                last_error = error
        if last_error:
            raise last_error
        return []

    @staticmethod
    def read_excel(path: Path):
        workbook = load_workbook(path, read_only=True, data_only=False)
        try:
            worksheet = workbook.active
            return [list(row) for row in worksheet.iter_rows(values_only=True)]
        finally:
            workbook.close()

    @staticmethod
    def is_blank(value):
        return value is None or (isinstance(value, str) and value.strip() == "")

    @classmethod
    def is_blank_row(cls, row):
        return all(cls.is_blank(value) for value in row)

    @staticmethod
    def trim_value(value):
        if isinstance(value, str):
            return value.strip()
        return value

    @classmethod
    def row_key(cls, row):
        # Compare normalized values so equivalent dates/numbers/strings can be hashed consistently.
        return tuple((type(value).__name__, str(value)) for value in row)

    def clean_data(self):
        if self.source_path is None:
            messagebox.showinfo("Нет таблицы", "Сначала открой CSV или XLSX-файл.")
            return

        if self.settings.get("confirm_before_clean", True):
            confirmed = messagebox.askyesno(
                "Подтверждение очистки",
                "Выполнить выбранные операции очистки для текущей таблицы?\n\n"
                "Исходный файл на диске не будет изменён.",
                parent=self.root,
            )
            if not confirmed:
                self.status_var.set("Очистка отменена пользователем.")
                return

        headers = list(self.headers)
        rows = [list(row) for row in self.rows]
        trimmed = 0
        removed_empty = 0
        removed_duplicates = 0

        if self.trim_spaces_var.get():
            new_headers = []
            for value in headers:
                new_value = self.trim_value(value)
                if new_value != value:
                    trimmed += 1
                new_headers.append(new_value)
            headers = new_headers

            new_rows = []
            for row in rows:
                new_row = []
                for value in row:
                    new_value = self.trim_value(value)
                    if new_value != value:
                        trimmed += 1
                    new_row.append(new_value)
                new_rows.append(new_row)
            rows = new_rows

        if self.remove_empty_var.get():
            kept_rows = []
            for row in rows:
                if self.is_blank_row(row):
                    removed_empty += 1
                else:
                    kept_rows.append(row)
            rows = kept_rows

        if self.remove_duplicates_var.get():
            seen = set()
            unique_rows = []
            for row in rows:
                key = self.row_key(row)
                if key in seen:
                    removed_duplicates += 1
                    continue
                seen.add(key)
                unique_rows.append(row)
            rows = unique_rows

        changed = headers != self.headers or rows != self.rows
        if not changed:
            self.trimmed_cells = trimmed
            self.removed_empty = removed_empty
            self.removed_duplicates = removed_duplicates
            self.status_var.set("Изменений не обнаружено — данные уже чистые или операции отключены.")
            if self.settings.get("show_operation_summary", True):
                messagebox.showinfo(
                    "Изменений нет",
                    "Выбранные операции не изменили таблицу.\n\n"
                    "Попробуй выбрать другие действия очистки.",
                    parent=self.root,
                )
            return

        # Keep a snapshot so the latest cleanup can be undone. Limit memory usage.
        self.undo_stack.append({
            "headers": list(self.headers),
            "rows": [list(row) for row in self.rows],
            "trimmed_cells": self.trimmed_cells,
            "removed_empty": self.removed_empty,
            "removed_duplicates": self.removed_duplicates,
        })
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

        self.headers = headers
        self.rows = rows
        self.trimmed_cells = trimmed
        self.removed_empty = removed_empty
        self.removed_duplicates = removed_duplicates
        self.update_undo_button()
        self.display_table()
        self.update_info()
        self.status_var.set(
            f"Очистка завершена: удалено пустых строк — {removed_empty}, "
            f"дубликатов — {removed_duplicates}, ячеек с изменёнными пробелами — {trimmed}."
        )
        if self.settings.get("show_operation_summary", True):
            messagebox.showinfo(
                "Очистка завершена",
                "Результат обновлён в таблице. Исходный файл не изменён.\n\n"
                f"Удалено пустых строк: {removed_empty}\n"
                f"Удалено дубликатов: {removed_duplicates}\n"
                f"Очищено ячеек от пробелов: {trimmed}\n\n"
                "Нажми «Сохранить как…», чтобы сохранить результат в новый файл.",
                parent=self.root,
            )

    def undo_changes(self):
        if not self.undo_stack:
            self.status_var.set("Нечего отменять.")
            return

        previous = self.undo_stack.pop()
        self.headers = list(previous["headers"])
        self.rows = [list(row) for row in previous["rows"]]
        self.trimmed_cells = previous["trimmed_cells"]
        self.removed_empty = previous["removed_empty"]
        self.removed_duplicates = previous["removed_duplicates"]

        self.display_table()
        self.update_info()
        self.update_undo_button()
        self.status_var.set("Последняя очистка отменена. Данные восстановлены в памяти.")
        if self.settings.get("show_operation_summary", True):
            messagebox.showinfo(
                "Изменения отменены",
                "Последняя очистка отменена. Таблица возвращена к предыдущему состоянию.\n\n"
                "Если ты уже сохранял очищенный файл, этот файл на диске не изменяется.",
                parent=self.root,
            )

    def save_as(self):
        if self.source_path is None:
            messagebox.showinfo("Нет таблицы", "Сначала открой CSV или XLSX-файл.")
            return

        suggested_name = f"{self.source_path.stem}_cleaned"
        filename = filedialog.asksaveasfilename(
            title="Сохранить очищенную таблицу",
            initialfile=suggested_name,
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Excel XLSX", "*.xlsx")],
        )
        if not filename:
            return

        path = Path(filename)
        try:
            if path.suffix.lower() == ".csv":
                with path.open("w", encoding="utf-8-sig", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([self.csv_value(value) for value in self.headers])
                    writer.writerows(
                        [[self.csv_value(value) for value in row] for row in self.rows]
                    )
            elif path.suffix.lower() == ".xlsx":
                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = "Cleaned data"
                worksheet.append([self.excel_value(value) for value in self.headers])
                for row in self.rows:
                    worksheet.append([self.excel_value(value) for value in row])
                workbook.save(path)
                workbook.close()
            else:
                messagebox.showerror("Неподдерживаемый формат", "Выбери расширение .csv или .xlsx.")
                return

            self.status_var.set(f"Сохранено: {path}")
            messagebox.showinfo("Сохранено", f"Очищенная таблица сохранена в новый файл:\n{path}")
        except Exception as error:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл:\n\n{error}")

    @staticmethod
    def csv_value(value):
        if value is None:
            return ""
        return str(value) if not isinstance(value, str) else value

    @staticmethod
    def excel_value(value):
        # openpyxl does not support arbitrary Python objects as cell values.
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)
