from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QTextEdit, QComboBox, QRadioButton, QButtonGroup,
    QDateEdit, QDoubleSpinBox, QDialogButtonBox, QLabel, QPushButton,
    QMessageBox
)
from PyQt5.QtCore import QDate, Qt


class TaskDialog(QDialog):
    def __init__(self, db, task=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.task = task  # None = create mode
        self._changed = False

        self.setWindowTitle("Редактировать задачу" if task else "Новая задача")
        self.setMinimumWidth(480)
        self._setup_ui()

        if task:
            self._populate_fields()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── Основное ──
        basic_box = QGroupBox("Основное")
        form = QFormLayout(basic_box)

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
        layout.addWidget(basic_box)

        # ── Категория и приоритет ──
        mid_layout = QHBoxLayout()

        cat_box = QGroupBox("Категория")
        cat_layout = QVBoxLayout(cat_box)
        self.cat_combo = QComboBox()
        self._load_categories()
        cat_layout.addWidget(self.cat_combo)
        mid_layout.addWidget(cat_box)

        pri_box = QGroupBox("Приоритет")
        pri_layout = QHBoxLayout(pri_box)
        self.pri_group = QButtonGroup(self)
        for i, (label, val) in enumerate([("Низкий", "low"),
                                           ("Средний", "medium"),
                                           ("Высокий", "high")]):
            rb = QRadioButton(label)
            rb.setProperty("value", val)
            if val == "medium":
                rb.setChecked(True)
            self.pri_group.addButton(rb, i)
            pri_layout.addWidget(rb)
        mid_layout.addWidget(pri_box)
        layout.addLayout(mid_layout)

        # ── Сроки ──
        date_box = QGroupBox("Сроки и время")
        date_form = QFormLayout(date_box)

        self.deadline_edit = QDateEdit()
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setDate(QDate.currentDate())
        self.deadline_edit.setSpecialValueText("Без дедлайна")
        self.deadline_edit.setMinimumDate(QDate(2000, 1, 1))

        self.no_deadline_btn = QPushButton("Очистить дедлайн")
        self.no_deadline_btn.setCheckable(True)
        self.no_deadline_btn.setChecked(True)
        self.no_deadline_btn.clicked.connect(self._toggle_deadline)

        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0, 999)
        self.hours_spin.setSuffix(" ч")

        dl_row = QHBoxLayout()
        dl_row.addWidget(self.deadline_edit)
        dl_row.addWidget(self.no_deadline_btn)

        date_form.addRow("Дедлайн:", dl_row)
        date_form.addRow("Оценка времени:", self.hours_spin)
        layout.addWidget(date_box)

        # ── Кнопки ──
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        self.buttons.accepted.connect(self._on_save)
        self.buttons.rejected.connect(self._on_cancel)
        layout.addWidget(self.buttons)

        # Validators
        self.title_edit.textChanged.connect(self._validate)
        self.title_edit.textChanged.connect(lambda: setattr(self, '_changed', True))
        self._validate()

    def _toggle_deadline(self, checked):
        self.deadline_edit.setEnabled(not checked)
        self.no_deadline_btn.setText("Без дедлайна" if checked else "Очистить дедлайн")

    def _load_categories(self):
        self.cat_combo.clear()
        self.cat_combo.addItem("Без категории", None)
        for cat in self.db.get_all_categories():
            self.cat_combo.addItem(cat["name"], cat["id"])

    def _populate_fields(self):
        t = self.task
        self.title_edit.setText(t["title"])
        self.desc_edit.setPlainText(t["description"] or "")

        for i in range(self.cat_combo.count()):
            if self.cat_combo.itemData(i) == t["category_id"]:
                self.cat_combo.setCurrentIndex(i)
                break

        pri_map = {"low": 0, "medium": 1, "high": 2}
        self.pri_group.button(pri_map.get(t["priority"], 1)).setChecked(True)

        if t["deadline"]:
            self.no_deadline_btn.setChecked(False)
            self._toggle_deadline(False)
            y, m, d = map(int, t["deadline"].split("-"))
            self.deadline_edit.setDate(QDate(y, m, d))
        
        self.hours_spin.setValue(t["estimated_hours"] or 0)
        self._changed = False

    def _validate(self):
        ok = bool(self.title_edit.text().strip())
        self.buttons.button(QDialogButtonBox.Save).setEnabled(ok)
        self.err_label.setVisible(not ok)
        self.title_edit.setStyleSheet(
            "" if ok else "border: 1px solid red;"
        )

    def _on_save(self):
        title = self.title_edit.text().strip()
        desc = self.desc_edit.toPlainText().strip()
        cat_id = self.cat_combo.currentData()
        priority = self.pri_group.checkedButton().property("value")
        deadline = (None if self.no_deadline_btn.isChecked()
                    else self.deadline_edit.date().toString("yyyy-MM-dd"))
        hours = self.hours_spin.value()

        if self.task:
            self.db.update_task(self.task["id"], title, desc, cat_id,
                                priority, deadline, hours)
        else:
            self.db.create_task(title, desc, cat_id, priority, deadline, hours)

        self.accept()

    def _on_cancel(self):
        if self._changed:
            reply = QMessageBox.question(
                self, "Несохранённые изменения",
                "Есть несохранённые изменения. Закрыть?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.reject()
