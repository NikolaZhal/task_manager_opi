from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLineEdit,
    QLabel, QProgressBar, QMessageBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

PRESET_COLORS = ["#4A90D9", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6"]
MAX_CATEGORIES = 9


class CategoryDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._edit_id = None

        self.setWindowTitle("Управление категориями")
        self.setMinimumWidth(520)
        self._setup_ui()
        self._load_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── Таблица существующих ──
        list_box = QGroupBox("Существующие категории")
        list_layout = QVBoxLayout(list_box)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Цвет", "Название", "% выполнения", ""])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 70)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        list_layout.addWidget(self.table)
        layout.addWidget(list_box)

        # ── Форма создания/редактирования ──
        edit_box = QGroupBox("Создать / Редактировать")
        edit_layout = QVBoxLayout(edit_box)

        name_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название категории *")
        name_row.addWidget(QLabel("Название:"))
        name_row.addWidget(self.name_edit)
        edit_layout.addLayout(name_row)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет:"))
        self.color_btns = []
        self.selected_color = PRESET_COLORS[0]
        for color in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            btn.setProperty("color", color)
            btn.clicked.connect(self._select_color)
            color_row.addWidget(btn)
            self.color_btns.append(btn)
        color_row.addStretch()
        edit_layout.addLayout(color_row)
        self._highlight_color(PRESET_COLORS[0])

        btn_row = QHBoxLayout()
        self.new_btn = QPushButton("+ Новая")
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setStyleSheet("background-color: #2E86C1; color: white;")
        btn_row.addWidget(self.new_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        edit_layout.addLayout(btn_row)
        layout.addWidget(edit_box)

        close_btns = QDialogButtonBox(QDialogButtonBox.Close)
        close_btns.rejected.connect(self.reject)
        layout.addWidget(close_btns)

        self.new_btn.clicked.connect(self._reset_form)
        self.save_btn.clicked.connect(self._on_save)
        self.name_edit.textChanged.connect(self._validate)
        self._validate()

    def _load_table(self):
        stats = self.db.get_stats()
        cat_map = {row["id"]: row for row in stats["cat_stats"]}

        cats = self.db.get_all_categories()
        self.table.setRowCount(len(cats))
        for row, cat in enumerate(cats):
            # Color cell
            color_item = QTableWidgetItem("  ")
            color_item.setBackground(QColor(cat["color"]))
            self.table.setItem(row, 0, color_item)

            # Name
            self.table.setItem(row, 1, QTableWidgetItem(cat["name"]))

            # Progress bar
            stat = cat_map.get(cat["id"])
            total = stat["total"] if stat else 0
            done = stat["done"] if stat else 0
            pct = int(done / total * 100) if total > 0 else 0
            bar = QProgressBar()
            bar.setValue(pct)
            bar.setFormat(f"{pct}% ({done}/{total})")
            if pct < 30:
                bar.setStyleSheet("QProgressBar::chunk { background: #E74C3C; }")
            self.table.setCellWidget(row, 2, bar)

            # Action buttons
            action_widget = QPushButton("✎ / 🗑")
            action_widget.setProperty("cat_id", cat["id"])
            action_widget.setProperty("cat_name", cat["name"])
            action_widget.setProperty("cat_color", cat["color"])

            edit_btn = QPushButton("✎")
            edit_btn.setFixedWidth(28)
            edit_btn.setProperty("cat_id", cat["id"])
            edit_btn.setProperty("cat_name", cat["name"])
            edit_btn.setProperty("cat_color", cat["color"])
            edit_btn.clicked.connect(self._edit_category)

            del_btn = QPushButton("🗑")
            del_btn.setFixedWidth(28)
            del_btn.setProperty("cat_id", cat["id"])
            del_btn.clicked.connect(self._delete_category)
            del_btn.setStyleSheet("color: #E74C3C;")

            cell_w = type("W", (), {})()
            from PyQt5.QtWidgets import QWidget
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(2, 2, 2, 2)
            h.addWidget(edit_btn)
            h.addWidget(del_btn)
            self.table.setCellWidget(row, 3, w)

    def _select_color(self):
        color = self.sender().property("color")
        self.selected_color = color
        self._highlight_color(color)

    def _highlight_color(self, selected):
        for btn in self.color_btns:
            c = btn.property("color")
            border = "3px solid #1E3A5F" if c == selected else "1px solid #ccc"
            btn.setStyleSheet(f"background-color: {c}; border-radius: 4px; border: {border};")

    def _validate(self):
        self.save_btn.setEnabled(bool(self.name_edit.text().strip()))

    def _reset_form(self):
        self._edit_id = None
        self.name_edit.clear()
        self._highlight_color(PRESET_COLORS[0])
        self.selected_color = PRESET_COLORS[0]

    def _edit_category(self):
        btn = self.sender()
        self._edit_id = btn.property("cat_id")
        self.name_edit.setText(btn.property("cat_name"))
        color = btn.property("cat_color")
        self.selected_color = color
        self._highlight_color(color)

    def _delete_category(self):
        cat_id = self.sender().property("cat_id")
        reply = QMessageBox.question(
            self, "Удалить категорию",
            "Удалить категорию? Задачи потеряют привязку к ней.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_category(cat_id)
            self._load_table()

    def _on_save(self):
        name = self.name_edit.text().strip()
        cats = self.db.get_all_categories()

        if self._edit_id is None and len(cats) >= MAX_CATEGORIES:
            QMessageBox.warning(self, "Лимит",
                                f"Максимум {MAX_CATEGORIES} категорий. Удалите неиспользуемые.")
            return

        try:
            if self._edit_id:
                self.db.update_category(self._edit_id, name, self.selected_color)
            else:
                self.db.create_category(name, self.selected_color)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        self._reset_form()
        self._load_table()
