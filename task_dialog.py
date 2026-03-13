"""
Диалоговое окно создания и редактирования задачи (Форма 3).

Поддерживает два режима работы:
  - создание новой задачи (task=None);
  - редактирование существующей задачи (task=<строка БД>).
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QTextEdit, QComboBox, QRadioButton, QButtonGroup,
    QDateEdit, QDoubleSpinBox, QDialogButtonBox, QLabel, QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import QDate


class TaskDialog(QDialog):
    """
    Диалог создания / редактирования задачи.

    Args:
        db (DatabaseManager): менеджер базы данных.
        task (sqlite3.Row | None): строка задачи для редактирования
            или None для создания новой.
        parent (QWidget | None): родительский виджет.
    """

    def __init__(self, db, task=None, parent=None) -> None:
        """
        Инициализирует диалог.

        Args:
            db (DatabaseManager): менеджер базы данных.
            task (sqlite3.Row | None): задача для редактирования или None.
            parent (QWidget | None): родительский виджет.
        """
        super().__init__(parent)
        self.db = db
        self.task = task
        self._changed = False  # флаг несохранённых изменений

        title = "Редактировать задачу" if task else "Новая задача"
        self.setWindowTitle(title)
        self.setMinimumWidth(480)

        self._setup_ui()

        # В режиме редактирования заполняем поля текущими данными
        if task:
            self._populate_fields()

    # ── Построение интерфейса ─────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """Создаёт и размещает все виджеты диалога."""
        layout = QVBoxLayout(self)

        layout.addWidget(self._build_basic_group())
        layout.addLayout(self._build_mid_row())
        layout.addWidget(self._build_date_group())
        layout.addWidget(self._build_buttons())

        # Подключаем валидатор к полю названия
        self.title_edit.textChanged.connect(self._validate)
        self.title_edit.textChanged.connect(lambda: setattr(self, "_changed", True))
        self._validate()

    def _build_basic_group(self) -> QGroupBox:
        """
        Создаёт группу «Основное» (название + описание).

        Returns:
            QGroupBox: готовая группа виджетов.
        """
        group = QGroupBox("Основное")
        form = QFormLayout(group)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Название задачи *")

        self.err_label = QLabel("Введите название задачи")
        self.err_label.setStyleSheet("color: red; font-size: 11px;")
        self.err_label.hide()

        self.desc_edit = QTextEdit()
        self.desc_edit.setFixedHeight(70)
        self.desc_edit.setPlaceholderText("Описание (необязательно)")

        form.addRow("Название *:", self.title_edit)
        form.addRow("", self.err_label)
        form.addRow("Описание:", self.desc_edit)
        return group

    def _build_mid_row(self) -> QHBoxLayout:
        """
        Создаёт строку с группами «Категория» и «Приоритет».

        Returns:
            QHBoxLayout: горизонтальный контейнер с двумя группами.
        """
        row = QHBoxLayout()

        # Группа категории
        cat_group = QGroupBox("Категория")
        cat_layout = QVBoxLayout(cat_group)
        self.cat_combo = QComboBox()
        self._load_categories()
        cat_layout.addWidget(self.cat_combo)
        row.addWidget(cat_group)

        # Группа приоритета (три радиокнопки)
        pri_group = QGroupBox("Приоритет")
        pri_layout = QHBoxLayout(pri_group)
        self.pri_group = QButtonGroup(self)

        for index, (label, value) in enumerate(
            [("Низкий", "low"), ("Средний", "medium"), ("Высокий", "high")]
        ):
            btn = QRadioButton(label)
            btn.setProperty("value", value)
            if value == "medium":
                btn.setChecked(True)  # «Средний» по умолчанию
            self.pri_group.addButton(btn, index)
            pri_layout.addWidget(btn)

        row.addWidget(pri_group)
        return row

    def _build_date_group(self) -> QGroupBox:
        """
        Создаёт группу «Сроки и время» (дедлайн + оценка часов).

        Returns:
            QGroupBox: готовая группа виджетов.
        """
        group = QGroupBox("Сроки и время")
        form = QFormLayout(group)

        # Поле даты
        self.deadline_edit = QDateEdit()
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setDate(QDate.currentDate())
        self.deadline_edit.setEnabled(False)  # по умолчанию дедлайн не задан

        # Флаг: True = дедлайн задан, False = без дедлайна
        self._has_deadline = False

        # Кнопка переключения
        self.no_deadline_btn = QPushButton("Без дедлайна")
        self.no_deadline_btn.setCheckable(False)
        self.no_deadline_btn.clicked.connect(self._toggle_deadline)

        # Оценка времени
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0, 999)
        self.hours_spin.setSuffix(" ч")

        deadline_row = QHBoxLayout()
        deadline_row.addWidget(self.deadline_edit)
        deadline_row.addWidget(self.no_deadline_btn)

        form.addRow("Дедлайн:", deadline_row)
        form.addRow("Оценка времени:", self.hours_spin)
        return group

    def _build_buttons(self) -> QDialogButtonBox:
        """
        Создаёт стандартные кнопки «Сохранить» и «Отмена».

        Returns:
            QDialogButtonBox: контейнер с кнопками.
        """
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self._on_cancel)
        self._save_button = buttons.button(QDialogButtonBox.Save)
        return buttons

    # ── Вспомогательные методы ────────────────────────────────────────────────

    def _load_categories(self) -> None:
        """Загружает список категорий из БД в выпадающий список."""
        self.cat_combo.clear()
        self.cat_combo.addItem("Без категории", None)
        for cat in self.db.get_all_categories():
            self.cat_combo.addItem(cat["name"], cat["id"])

    def _populate_fields(self) -> None:
        """Заполняет поля формы данными редактируемой задачи."""
        task = self.task
        self.title_edit.setText(task["title"])
        self.desc_edit.setPlainText(task["description"] or "")

        # Устанавливаем нужную категорию в комбобоксе
        for i in range(self.cat_combo.count()):
            if self.cat_combo.itemData(i) == task["category_id"]:
                self.cat_combo.setCurrentIndex(i)
                break

        # Устанавливаем радиокнопку приоритета
        priority_index = {"low": 0, "medium": 1, "high": 2}
        self.pri_group.button(
            priority_index.get(task["priority"], 1)
        ).setChecked(True)

        # Восстанавливаем дедлайн
        if task["deadline"]:
            self._has_deadline = True
            self.deadline_edit.setEnabled(True)
            self.no_deadline_btn.setText("Убрать дедлайн")
            self.no_deadline_btn.setStyleSheet(
                "background: #2D3BDB; color: white; border: none;"
            )
            year, month, day = map(int, task["deadline"].split("-"))
            self.deadline_edit.setDate(QDate(year, month, day))

        self.hours_spin.setValue(task["estimated_hours"] or 0)
        self._changed = False  # сбрасываем флаг после заполнения

    def _toggle_deadline(self) -> None:
        """
        Включает или выключает поле ввода дедлайна.

        Переключает внутренний флаг _has_deadline и обновляет
        состояние виджетов соответственно.
        """
        self._has_deadline = not self._has_deadline
        self.deadline_edit.setEnabled(self._has_deadline)
        if self._has_deadline:
            self.no_deadline_btn.setText("Убрать дедлайн")
            self.no_deadline_btn.setStyleSheet(
                "background: #2D3BDB; color: white; border: none;"
            )
        else:
            self.no_deadline_btn.setText("Без дедлайна")
            self.no_deadline_btn.setStyleSheet("")

    def _validate(self) -> None:
        """Активирует кнопку «Сохранить» только если название не пустое."""
        is_valid = bool(self.title_edit.text().strip())
        self._save_button.setEnabled(is_valid)
        self.err_label.setVisible(not is_valid)
        self.title_edit.setStyleSheet(
            "" if is_valid else "border: 1px solid red;"
        )

    # ── Обработчики кнопок ────────────────────────────────────────────────────

    def _on_save(self) -> None:
        """Сохраняет задачу в БД и закрывает диалог с результатом Accepted."""
        title = self.title_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        category_id = self.cat_combo.currentData()
        priority = self.pri_group.checkedButton().property("value")
        deadline = (
            self.deadline_edit.date().toString("yyyy-MM-dd")
            if self._has_deadline
            else None
        )
        hours = self.hours_spin.value()

        if self.task:
            self.db.update_task(
                self.task["id"], title, description,
                category_id, priority, deadline, hours,
            )
        else:
            self.db.create_task(
                title, description, category_id, priority, deadline, hours
            )

        self.accept()

    def _on_cancel(self) -> None:
        """
        Закрывает диалог. Если есть несохранённые изменения —
        запрашивает подтверждение у пользователя.
        """
        if self._changed:
            reply = QMessageBox.question(
                self,
                "Несохранённые изменения",
                "Есть несохранённые изменения. Закрыть?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return
        self.reject()
