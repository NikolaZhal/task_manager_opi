"""
Диалоговое окно управления категориями задач (Форма 4).

Позволяет создавать, переименовывать и удалять категории,
а также просматривать процент выполнения задач по каждой из них.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLineEdit, QLabel, QProgressBar,
    QMessageBox, QDialogButtonBox, QWidget,
)
from PyQt5.QtGui import QColor


# Предустановленные цвета для категорий
PRESET_COLORS = ["#4A90D9", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6"]

# Максимальное число категорий (дублирует константу в DatabaseManager)
MAX_CATEGORIES = 9


class CategoryDialog(QDialog):
    """
    Диалог управления категориями.

    Отображает таблицу существующих категорий с прогрессом выполнения
    и форму для добавления / редактирования записей.

    Args:
        db (DatabaseManager): менеджер базы данных.
        parent (QWidget | None): родительский виджет.
    """

    def __init__(self, db, parent=None) -> None:
        """
        Инициализирует диалог управления категориями.

        Args:
            db (DatabaseManager): менеджер базы данных.
            parent (QWidget | None): родительский виджет.
        """
        super().__init__(parent)
        self.db = db
        self._edit_id: int | None = None  # ID редактируемой категории

        self.setWindowTitle("Управление категориями")
        self.setMinimumWidth(540)

        self._setup_ui()
        self._load_table()

    # ── Построение интерфейса ─────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """Создаёт и размещает все виджеты диалога."""
        layout = QVBoxLayout(self)
        layout.addWidget(self._build_list_group())
        layout.addWidget(self._build_edit_group())

        close_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.reject)
        layout.addWidget(close_buttons)

    def _build_list_group(self) -> QGroupBox:
        """
        Создаёт группу с таблицей существующих категорий.

        Returns:
            QGroupBox: группа с QTableWidget внутри.
        """
        group = QGroupBox("Существующие категории")
        layout = QVBoxLayout(group)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Цвет", "Название", "% выполнения", ""])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 80)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)
        return group

    def _build_edit_group(self) -> QGroupBox:
        """
        Создаёт группу с формой создания/редактирования категории.

        Returns:
            QGroupBox: группа с полем ввода и кнопками цветов.
        """
        group = QGroupBox("Создать / Редактировать")
        layout = QVBoxLayout(group)

        # Строка ввода названия
        name_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название категории *")
        name_row.addWidget(QLabel("Название:"))
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        # Строка выбора цвета
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет:"))
        self.color_buttons: list[QPushButton] = []
        self.selected_color = PRESET_COLORS[0]

        for color in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setProperty("color", color)
            btn.clicked.connect(self._on_color_selected)
            self.color_buttons.append(btn)
            color_row.addWidget(btn)

        color_row.addStretch()
        layout.addLayout(color_row)
        self._highlight_color(PRESET_COLORS[0])

        # Кнопки действий
        btn_row = QHBoxLayout()
        new_btn = QPushButton("+ Новая")
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setStyleSheet(
            "background-color: #2E86C1; color: white; font-weight: bold;"
        )
        new_btn.clicked.connect(self._reset_form)
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(new_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        self.name_edit.textChanged.connect(self._validate)
        self._validate()
        return group

    # ── Заполнение таблицы ────────────────────────────────────────────────────

    def _load_table(self) -> None:
        """Перечитывает данные из БД и перестраивает таблицу категорий."""
        stats = self.db.get_stats()
        # Преобразуем список строк в словарь {id: row} для быстрого доступа
        cat_stats_map = {row["id"]: row for row in stats["cat_stats"]}

        categories = self.db.get_all_categories()
        self.table.setRowCount(len(categories))

        for row_idx, cat in enumerate(categories):
            self._fill_table_row(row_idx, cat, cat_stats_map.get(cat["id"]))

    def _fill_table_row(self, row_idx: int, cat, stat) -> None:
        """
        Заполняет одну строку таблицы данными категории.

        Args:
            row_idx (int): номер строки.
            cat (sqlite3.Row): строка категории из БД.
            stat (sqlite3.Row | None): статистика выполнения для этой категории.
        """
        # Ячейка цвета
        color_item = QTableWidgetItem("  ")
        color_item.setBackground(QColor(cat["color"]))
        self.table.setItem(row_idx, 0, color_item)

        # Название
        self.table.setItem(row_idx, 1, QTableWidgetItem(cat["name"]))

        # Прогресс-бар
        total = stat["total"] if stat else 0
        done = stat["done"] if stat else 0
        percent = int(done / total * 100) if total > 0 else 0

        bar = QProgressBar()
        bar.setValue(percent)
        bar.setFormat(f"{percent}% ({done}/{total})")
        self.table.setCellWidget(row_idx, 2, bar)

        # Кнопки «Изменить» и «Удалить»
        self.table.setCellWidget(
            row_idx, 3, self._make_action_cell(cat)
        )

    def _make_action_cell(self, cat) -> QWidget:
        """
        Создаёт виджет с кнопками «✎» и «🗑» для строки таблицы.

        Args:
            cat (sqlite3.Row): строка категории.

        Returns:
            QWidget: контейнер с двумя кнопками.
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        edit_btn = QPushButton("✎")
        edit_btn.setFixedWidth(30)
        edit_btn.setProperty("cat_id",    cat["id"])
        edit_btn.setProperty("cat_name",  cat["name"])
        edit_btn.setProperty("cat_color", cat["color"])
        edit_btn.clicked.connect(self._on_edit_click)

        del_btn = QPushButton("🗑")
        del_btn.setFixedWidth(30)
        del_btn.setStyleSheet("color: #E74C3C;")
        del_btn.setProperty("cat_id", cat["id"])
        del_btn.clicked.connect(self._on_delete_click)

        layout.addWidget(edit_btn)
        layout.addWidget(del_btn)
        return container

    # ── Работа с цветом ───────────────────────────────────────────────────────

    def _on_color_selected(self) -> None:
        """Запоминает выбранный цвет и обновляет визуальное выделение кнопок."""
        self.selected_color = self.sender().property("color")
        self._highlight_color(self.selected_color)

    def _highlight_color(self, selected: str) -> None:
        """
        Выделяет активную кнопку цвета рамкой.

        Args:
            selected (str): HEX-код выбранного цвета.
        """
        for btn in self.color_buttons:
            color = btn.property("color")
            border = (
                "3px solid #1E3A5F" if color == selected else "1px solid #ccc"
            )
            btn.setStyleSheet(
                f"background-color: {color}; border-radius: 4px; border: {border};"
            )

    # ── Обработчики событий ───────────────────────────────────────────────────

    def _validate(self) -> None:
        """Активирует кнопку «Сохранить» только если название не пустое."""
        self.save_btn.setEnabled(bool(self.name_edit.text().strip()))

    def _reset_form(self) -> None:
        """Сбрасывает форму в состояние создания новой категории."""
        self._edit_id = None
        self.name_edit.clear()
        self.selected_color = PRESET_COLORS[0]
        self._highlight_color(PRESET_COLORS[0])

    def _on_edit_click(self) -> None:
        """Заполняет форму данными выбранной категории для редактирования."""
        btn = self.sender()
        self._edit_id = btn.property("cat_id")
        self.name_edit.setText(btn.property("cat_name"))
        self.selected_color = btn.property("cat_color")
        self._highlight_color(self.selected_color)

    def _on_delete_click(self) -> None:
        """Запрашивает подтверждение и удаляет категорию из БД."""
        cat_id = self.sender().property("cat_id")
        reply = QMessageBox.question(
            self,
            "Удалить категорию",
            "Удалить категорию? Задачи потеряют привязку к ней.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_category(cat_id)
            self._load_table()

    def _on_save(self) -> None:
        """Создаёт новую или обновляет существующую категорию в БД."""
        name = self.name_edit.text().strip()
        categories = self.db.get_all_categories()

        # Проверяем лимит только при создании новой категории
        if self._edit_id is None and len(categories) >= MAX_CATEGORIES:
            QMessageBox.warning(
                self,
                "Лимит категорий",
                f"Максимальное число категорий: {MAX_CATEGORIES}. "
                "Удалите неиспользуемые.",
            )
            return

        try:
            if self._edit_id is not None:
                self.db.update_category(self._edit_id, name, self.selected_color)
            else:
                self.db.create_category(name, self.selected_color)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))
            return

        self._reset_form()
        self._load_table()
