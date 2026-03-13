"""
Главное окно приложения «Система управления задачами».

Содержит:
  - Dashboard с виджетами статистики (Форма 1);
  - Список задач с фильтрацией и сортировкой (Форма 2);
  - Навигационную панель и панель инструментов.
"""

from datetime import date

from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDockWidget, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
    QStatusBar, QTableWidget, QTableWidgetItem, QToolBar, QVBoxLayout,
    QWidget,
)

from category_dialog import CategoryDialog
from task_dialog import TaskDialog

# ── Константы приоритетов ─────────────────────────────────────────────────────
PRIORITY_LABELS = {
    "low":    "↓  Низкий",
    "medium": "→  Средний",
    "high":   "↑  Высокий",
}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PRIORITY_COLORS = {
    "low":    "#10B981",
    "medium": "#F59E0B",
    "high":   "#EF4444",
}

# ── Глобальный стиль приложения (тёмная тема) ─────────────────────────────────
APP_STYLESHEET = """
* { box-sizing: border-box; }

QMainWindow, QWidget {
    background: #0F1117;
    color: #CBD5E1;
    font-family: 'Segoe UI', Tahoma, sans-serif;
    font-size: 15px;
}
QDockWidget { background: #0F1117; border: none; }
QDockWidget::title {
    background: #151820; padding: 10px 16px;
    color: #64748B; font-size: 12px; font-weight: 700;
    letter-spacing: 1.5px; border-bottom: 1px solid #1E2535;
}
QListWidget { background: #151820; border: none; outline: none; padding: 6px 0; }
QListWidget::item {
    height: 44px; padding: 0 16px; margin: 1px 6px;
    border-radius: 8px; color: #64748B; font-size: 14px;
}
QListWidget::item:hover  { background: #1E2535; color: #94A3B8; }
QListWidget::item:selected { background: #2D3BDB; color: #fff; font-weight: 600; }
QToolBar {
    background: #151820; border: none;
    border-bottom: 1px solid #1E2535; padding: 6px 14px; spacing: 8px;
}
QToolBar::separator { background: #1E2535; width: 1px; margin: 4px 2px; }
QMenuBar { background: #151820; color: #64748B; border-bottom: 1px solid #1E2535; font-size: 14px; }
QMenuBar::item:selected { background: #1E2535; border-radius: 4px; color: #CBD5E1; }
QMenu { background: #1A1F2E; border: 1px solid #2D3748; border-radius: 8px; padding: 4px; color: #CBD5E1; font-size: 14px; }
QMenu::item { padding: 9px 20px; border-radius: 4px; }
QMenu::item:selected { background: #2D3BDB; color: #fff; }
QPushButton {
    background: #1E2535; color: #94A3B8;
    border: 1px solid #2D3748; border-radius: 7px;
    padding: 8px 18px; font-size: 14px;
}
QPushButton:hover { background: #252D42; color: #E2E8F0; border-color: #3D4F7C; }
QPushButton:pressed { background: #1A2030; }
QPushButton#primary {
    background: #2D3BDB; color: #fff; border: none;
    font-weight: 600; padding: 9px 24px; font-size: 14px;
}
QPushButton#primary:hover { background: #3D4BE8; }
QPushButton#edit_btn {
    background: #1A2535; color: #60A5FA; border: 1px solid #1E3A5F;
    border-radius: 6px; font-size: 16px; font-weight: bold;
}
QPushButton#edit_btn:hover { background: #1E3A5F; color: #93C5FD; }
QPushButton#del_btn {
    background: #1A1520; color: #F87171; border: 1px solid #3D1515;
    border-radius: 6px; font-size: 15px; font-weight: bold;
}
QPushButton#del_btn:hover { background: #3D1515; color: #FCA5A5; }
QPushButton#small { padding: 7px 14px; font-size: 13px; border-radius: 6px; }
QLineEdit, QTextEdit, QDoubleSpinBox, QSpinBox {
    background: #1A1F2E; color: #E2E8F0;
    border: 1px solid #2D3748; border-radius: 7px;
    padding: 9px 13px; font-size: 14px;
    selection-background-color: #2D3BDB;
}
QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus { border-color: #2D3BDB; }
QComboBox {
    background: #1A1F2E; color: #94A3B8;
    border: 1px solid #2D3748; border-radius: 7px;
    padding: 7px 13px; font-size: 14px;
}
QComboBox:focus { border-color: #2D3BDB; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: #1A1F2E; border: 1px solid #2D3BDB;
    selection-background-color: #2D3BDB; color: #CBD5E1;
    border-radius: 4px; font-size: 14px;
}
QDateEdit {
    background: #1A1F2E; color: #CBD5E1;
    border: 1px solid #2D3748; border-radius: 7px;
    padding: 8px 13px; font-size: 14px;
}
QDateEdit:focus { border-color: #2D3BDB; }
QTableWidget {
    background: #0F1117; border: none; outline: none;
    gridline-color: transparent; alternate-background-color: #11141C;
    font-size: 14px;
}
QTableWidget::item { padding: 0 12px; color: #CBD5E1; background: transparent; }
QTableWidget::item:selected { background: #1E2D52; color: #E2E8F0; }
QTableWidget::item:hover { background: #171D2D; }
QHeaderView { background: #0F1117; }
QHeaderView::section {
    background: #151820; color: #64748B;
    font-size: 13px; font-weight: 700; letter-spacing: 0.4px;
    padding: 11px 12px; border: none;
    border-bottom: 2px solid #1E2535; border-right: 1px solid #1E2535;
}
QGroupBox {
    background: #11141C; border: 1px solid #1E2535;
    border-radius: 12px; margin-top: 22px; padding: 16px 12px 10px; color: #64748B;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 14px; top: -2px;
    padding: 0 6px; color: #64748B; font-size: 12px;
    font-weight: 700; letter-spacing: 1px; background: #0F1117;
}
QProgressBar {
    background: #1A1F2E; border: none; border-radius: 5px;
    height: 8px; color: transparent;
}
QProgressBar::chunk { background: #2D3BDB; border-radius: 5px; }
QScrollBar:vertical { background: #0F1117; width: 6px; border: none; }
QScrollBar:horizontal { background: #0F1117; height: 6px; border: none; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #2D3748; border-radius: 3px; min-height: 20px;
}
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QCheckBox { color: #64748B; spacing: 0; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 4px; border: 2px solid #2D3748; background: transparent;
}
QCheckBox::indicator:hover { border-color: #2D3BDB; }
QCheckBox::indicator:checked { background: #2D3BDB; border-color: #2D3BDB; }
QStatusBar {
    background: #151820; color: #64748B;
    border-top: 1px solid #1E2535; font-size: 13px; padding: 0 14px;
}
QDialog { background: #11141C; }
QMessageBox { background: #11141C; }
QMessageBox QLabel { background: transparent; color: #CBD5E1; font-size: 14px; }
QMessageBox QPushButton { min-width: 90px; }
QRadioButton { color: #64748B; spacing: 8px; font-size: 14px; }
QRadioButton::indicator {
    width: 17px; height: 17px; border-radius: 9px;
    border: 2px solid #2D3748; background: transparent;
}
QRadioButton::indicator:checked { background: #2D3BDB; border-color: #2D3BDB; }
QRadioButton:checked { color: #E2E8F0; font-weight: 600; }
QScrollArea { border: none; background: transparent; }
QLabel { font-size: 14px; }
"""


# ── Вспомогательный виджет: карточка статистики ───────────────────────────────

class StatCard(QFrame):
    """
    Карточка с одним показателем на Dashboard.

    Отображает иконку, числовое значение и подпись,
    выделена цветной левой полосой.

    Args:
        icon (str): эмодзи-иконка.
        title (str): подпись под числом.
        accent (str): HEX-цвет акцентной полосы и числа.
    """

    def __init__(self, icon: str, title: str, accent: str = "#2D3BDB") -> None:
        """
        Инициализирует карточку.

        Args:
            icon (str): эмодзи-иконка.
            title (str): подпись под числом.
            accent (str): HEX-цвет акцентной полосы и числа.
        """
        super().__init__()
        self.setFixedHeight(86)
        self.setStyleSheet(
            f"QFrame {{ background: #11141C; border: 1px solid #1E2535; "
            f"border-left: 3px solid {accent}; border-radius: 10px; }}"
            f"QLabel {{ border: none; background: transparent; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        # Иконка
        top_row = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {accent}; font-size: 15px;")
        top_row.addWidget(icon_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Числовое значение
        self._value_label = QLabel("0")
        self._value_label.setStyleSheet(
            f"color: {accent}; font-size: 24px; font-weight: 700;"
        )
        layout.addWidget(self._value_label)

        # Текстовая подпись
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(title_label)

    def set_value(self, value: int) -> None:
        """
        Обновляет отображаемое число.

        Args:
            value (int): новое значение.
        """
        self._value_label.setText(str(value))


# ── Вспомогательные функции создания cell-виджетов ────────────────────────────

def _make_checkbox_cell(checked: bool, callback) -> QWidget:
    """
    Создаёт прозрачный виджет с центрированным QCheckBox для ячейки таблицы.

    Args:
        checked (bool): начальное состояние чекбокса.
        callback: функция, вызываемая при изменении состояния.

    Returns:
        QWidget: контейнер с чекбоксом.
    """
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignCenter)

    checkbox = QCheckBox()
    checkbox.setChecked(checked)
    checkbox.stateChanged.connect(callback)
    layout.addWidget(checkbox)
    return container


def _make_action_cell(task_id: int, edit_callback, delete_callback) -> QWidget:
    """
    Создаёт прозрачный виджет с кнопками «✎» и «✕» для ячейки таблицы.

    Args:
        task_id (int): идентификатор задачи, передаётся кнопкам через Qt-свойство.
        edit_callback: слот кнопки редактирования.
        delete_callback: слот кнопки удаления.

    Returns:
        QWidget: контейнер с двумя кнопками.
    """
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(6, 4, 6, 4)
    layout.setSpacing(16)

    edit_btn = QPushButton("✎")
    edit_btn.setObjectName("edit_btn")
    edit_btn.setFixedSize(34, 34)
    edit_btn.setCursor(Qt.PointingHandCursor)
    edit_btn.setProperty("task_id", task_id)
    edit_btn.clicked.connect(edit_callback)

    del_btn = QPushButton("✕")
    del_btn.setObjectName("del_btn")
    del_btn.setFixedSize(34, 34)
    del_btn.setCursor(Qt.PointingHandCursor)
    del_btn.setProperty("task_id", task_id)
    del_btn.clicked.connect(delete_callback)

    layout.addWidget(edit_btn)
    layout.addWidget(del_btn)
    return container


# ── Главное окно ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """
    Главное окно приложения.

    Содержит левую навигационную панель (Dock),
    панель инструментов и центральный стек из двух экранов:
      - индекс 0 — Dashboard;
      - индекс 1 — Список задач.

    Args:
        db (DatabaseManager): менеджер базы данных.
    """

    def __init__(self, db) -> None:
        """
        Инициализирует главное окно и строит весь интерфейс.

        Args:
            db (DatabaseManager): менеджер базы данных.
        """
        super().__init__()
        self.db = db
        self.setWindowTitle("Task Manager")
        self.setMinimumSize(1100, 680)
        self.setStyleSheet(APP_STYLESHEET)

        # Таймер для отслеживания времени (не активен при открытии)
        self._timer = QTimer(self)
        self._timer_secs = 0
        self._timer.timeout.connect(self._on_timer_tick)

        # Кеш задач для фильтрации без повторных запросов к БД
        self._all_tasks: list = []
        # Текущий активный раздел навигации — чтобы refresh знал какую выборку грузить
        self._current_view: str = "dashboard"

        # Построение UI
        self._build_menubar()
        self._build_toolbar()
        self._build_navigation_dock()
        self._build_central_widget()
        self._build_statusbar()

        # Первоначальная загрузка данных
        self.refresh()

    # ── Построение UI ─────────────────────────────────────────────────────────

    def _build_menubar(self) -> None:
        """Создаёт строку меню с разделами «Файл», «Задачи», «Настройки»."""
        mb = self.menuBar()
        mb.addMenu("Файл").addAction("Выход", self.close)
        mb.addMenu("Задачи").addAction("Новая задача", self._open_create_dialog)
        mb.addMenu("Настройки").addAction(
            "Управление категориями", self._open_categories_dialog
        )

    def _build_toolbar(self) -> None:
        """Создаёт панель инструментов с кнопкой «+ Новая задача» и строкой поиска."""
        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        # Кнопка создания задачи
        new_btn = QPushButton("  +  Новая задача")
        new_btn.setObjectName("primary")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._open_create_dialog)
        toolbar.addWidget(new_btn)
        toolbar.addSeparator()

        # Растяжка слева — прижимает поиск к центру/правой стороне
        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer_left)

        # Строка поиска — фиксированная ширина, не растягивается
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Поиск задач...")
        self.search_edit.setFixedWidth(300)
        self.search_edit.setMaximumWidth(300)
        self.search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_edit)

        # Растяжка справа
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer_right)

        # Кнопка категорий
        cat_btn = QPushButton("⚙  Категории")
        cat_btn.setObjectName("small")
        cat_btn.clicked.connect(self._open_categories_dialog)
        toolbar.addWidget(cat_btn)

    def _build_navigation_dock(self) -> None:
        """Создаёт левую панель навигации (QDockWidget с QListWidget)."""
        dock = QDockWidget("НАВИГАЦИЯ", self)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock.setMinimumWidth(210)

        self.nav_list = QListWidget()
        nav_items = [
            ("🏠   Главная",            "dashboard"),
            ("📋   Все задачи",         "all"),
            ("📅   На сегодня",         "today"),
            ("⚠   Просроченные",       "overdue"),
            ("⬆   Высокий приоритет",  "high"),
        ]
        for label, key in nav_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.nav_list.addItem(item)

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        dock.setWidget(self.nav_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _build_central_widget(self) -> None:
        """Создаёт стек из двух экранов: Dashboard и Список задач."""
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.stack.addWidget(self._build_dashboard())   # индекс 0
        self.stack.addWidget(self._build_task_list())   # индекс 1

    def _build_statusbar(self) -> None:
        """Создаёт строку состояния в нижней части окна."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _build_dashboard(self) -> QScrollArea:
        """
        Строит экран Dashboard со статистическими карточками,
        общим прогресс-баром, прогрессом по категориям и таблицей задач на сегодня.

        Returns:
            QScrollArea: прокручиваемый контейнер с содержимым Dashboard.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        root = QWidget()
        root.setStyleSheet("background: #0F1117;")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(18)

        # Заголовок
        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #E2E8F0;")
        layout.addWidget(header)

        # Ряд карточек-счётчиков
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_total   = StatCard("📋", "Всего задач",  "#6366F1")
        self.card_done    = StatCard("✅", "Выполнено",    "#10B981")
        self.card_overdue = StatCard("⚠",  "Просрочено",  "#EF4444")
        self.card_today   = StatCard("📅", "На сегодня",   "#F59E0B")
        for card in (self.card_total, self.card_done, self.card_overdue, self.card_today):
            cards_row.addWidget(card)
        layout.addLayout(cards_row)

        # Общий прогресс
        layout.addWidget(self._build_progress_frame())

        # Нижняя строка: категории слева, задачи на сегодня справа
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)
        bottom_row.addWidget(self._build_category_group(), 1)
        bottom_row.addWidget(self._build_today_group(), 2)
        layout.addLayout(bottom_row)

        layout.addStretch()
        scroll.setWidget(root)
        return scroll

    def _build_progress_frame(self) -> QFrame:
        """
        Создаёт фрейм с общим прогресс-баром.

        Returns:
            QFrame: фрейм с надписью «Общий прогресс» и QProgressBar.
        """
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:#11141C;border:1px solid #1E2535;border-radius:12px;}"
            "QLabel{border:none;background:transparent;}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Строка с заголовком и процентом
        header_row = QHBoxLayout()
        left_label = QLabel("Общий прогресс")
        left_label.setStyleSheet("color:#94A3B8;font-weight:600;")
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setStyleSheet(
            "color:#6366F1;font-weight:700;"
        )
        header_row.addWidget(left_label)
        header_row.addStretch()
        header_row.addWidget(self.progress_percent_label)

        self.progress_all = QProgressBar()
        self.progress_all.setFixedHeight(10)
        self.progress_all.setTextVisible(False)

        layout.addLayout(header_row)
        layout.addWidget(self.progress_all)
        return frame

    def _build_category_group(self) -> QGroupBox:
        """
        Создаёт группу «ПО КАТЕГОРИЯМ» с динамическими прогресс-барами.

        Returns:
            QGroupBox: группа с вертикальным layout для полос прогресса.
        """
        group = QGroupBox("ПО КАТЕГОРИЯМ")
        self.cat_layout = QVBoxLayout(group)
        self.cat_layout.setSpacing(10)
        return group

    def _build_today_group(self) -> QGroupBox:
        """
        Создаёт группу «ЗАДАЧИ НА СЕГОДНЯ» с таблицей и кнопкой перехода.

        Returns:
            QGroupBox: группа с QTableWidget и кнопкой «Все задачи →».
        """
        group = QGroupBox("ЗАДАЧИ НА СЕГОДНЯ")
        layout = QVBoxLayout(group)

        self.today_table = self._create_table(
            headers=["", "Задача", "Приоритет"],
            col_widths=[36, -1, 110],
        )
        layout.addWidget(self.today_table)

        go_btn = QPushButton("Все задачи  →")
        go_btn.setObjectName("small")
        go_btn.clicked.connect(lambda: self._switch_view("all"))
        layout.addWidget(go_btn, alignment=Qt.AlignRight)
        return group

    # ── Список задач ──────────────────────────────────────────────────────────

    def _build_task_list(self) -> QWidget:
        """
        Строит экран «Список задач» с фильтрами и таблицей задач.

        Returns:
            QWidget: корневой виджет экрана.
        """
        widget = QWidget()
        widget.setStyleSheet("background:#0F1117;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 22, 24, 16)
        layout.setSpacing(14)

        # Заголовок
        header = QLabel("Список задач")
        header.setStyleSheet("font-size:22px;font-weight:700;color:#E2E8F0;")
        layout.addWidget(header)

        # Панель фильтров
        layout.addWidget(self._build_filter_bar())

        # Счётчик результатов
        self.filter_count_label = QLabel("")
        self.filter_count_label.setStyleSheet(
            "color:#475569;font-size:12px;padding-left:2px;"
        )
        layout.addWidget(self.filter_count_label)

        # Таблица задач
        self.task_table = self._create_table(
            headers=["", "Название", "Категория", "Приоритет", "Дедлайн", ""],
            col_widths=[48, -1, 140, 130, 115, 110],
        )
        self.task_table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(self.task_table)

        return widget

    def _build_filter_bar(self) -> QFrame:
        """
        Создаёт панель фильтрации: выбор категории, приоритета, сортировки.

        Returns:
            QFrame: фрейм с выпадающими списками и кнопкой сброса.
        """
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:#11141C;border:1px solid #1E2535;border-radius:10px;}"
            "QLabel{border:none;background:transparent;color:#475569;font-size:12px;}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        # Фильтр по категории
        self.filter_cat_combo = QComboBox()
        self.filter_cat_combo.addItem("Все категории", None)
        self.filter_cat_combo.currentIndexChanged.connect(self._apply_filters)

        # Фильтр по приоритету
        self.filter_pri_combo = QComboBox()
        for label, value in [
            ("Все приоритеты", None),
            ("↑  Высокий", "high"),
            ("→  Средний", "medium"),
            ("↓  Низкий",  "low"),
        ]:
            self.filter_pri_combo.addItem(label, value)
        self.filter_pri_combo.currentIndexChanged.connect(self._apply_filters)

        # Сортировка
        self.sort_combo = QComboBox()
        for label, value in [
            ("По дедлайну",   "deadline"),
            ("По приоритету", "priority"),
            ("По дате",       "created_at"),
        ]:
            self.sort_combo.addItem(label, value)
        self.sort_combo.currentIndexChanged.connect(self._apply_filters)

        # Кнопка сброса
        reset_btn = QPushButton("Сбросить")
        reset_btn.setObjectName("small")
        reset_btn.clicked.connect(self._reset_filters)

        for text, combo in [
            ("Категория:", self.filter_cat_combo),
            ("Приоритет:", self.filter_pri_combo),
            ("Сортировка:", self.sort_combo),
        ]:
            layout.addWidget(QLabel(text))
            layout.addWidget(combo)

        layout.addStretch()
        layout.addWidget(reset_btn)
        return frame

    # ── Таблицы ───────────────────────────────────────────────────────────────

    def _create_table(self, headers: list, col_widths: list) -> QTableWidget:
        """
        Создаёт настроенный QTableWidget с заданными заголовками и шириной столбцов.

        Args:
            headers (list[str]): подписи заголовков столбцов.
            col_widths (list[int]): ширины столбцов в пикселях;
                значение -1 означает растяжку (Stretch).

        Returns:
            QTableWidget: готовая таблица без строк данных.
        """
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.NoFocus)
        table.horizontalHeader().setHighlightSections(False)

        for i, width in enumerate(col_widths):
            if width == -1:
                table.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.Stretch
                )
            else:
                table.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.Fixed
                )
                table.setColumnWidth(i, width)
        return table

    # ── Обновление Dashboard ──────────────────────────────────────────────────

    def _refresh_dashboard(self) -> None:
        """Загружает статистику из БД и обновляет все виджеты Dashboard."""
        stats = self.db.get_stats()

        # Обновляем карточки-счётчики
        self.card_total.set_value(stats["total"])
        self.card_done.set_value(stats["done"])
        self.card_overdue.set_value(stats["overdue"])
        self.card_today.set_value(stats["today"])

        # Общий прогресс
        percent = (
            int(stats["done"] / stats["total"] * 100)
            if stats["total"] > 0 else 0
        )
        self.progress_all.setValue(percent)
        self.progress_percent_label.setText(f"{percent}%")

        self._refresh_category_bars(stats["cat_stats"])
        self._refresh_today_table()

    def _refresh_category_bars(self, cat_stats: list) -> None:
        """
        Перестраивает строки прогресса по категориям.

        Args:
            cat_stats (list[sqlite3.Row]): статистика по категориям из get_stats().
        """
        # Удаляем старые виджеты
        for i in reversed(range(self.cat_layout.count())):
            widget = self.cat_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Добавляем новые строки
        for row in cat_stats:
            total = row["total"]
            done = row["done"] or 0
            percent = int(done / total * 100) if total > 0 else 0

            frame = QFrame()
            frame.setStyleSheet(
                "QFrame{background:transparent;border:none;}"
                "QLabel{border:none;background:transparent;}"
            )
            layout = QHBoxLayout(frame)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            # Цветная точка
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{row['color']};font-size:8px;")
            dot.setFixedWidth(12)

            # Название категории
            name_label = QLabel(row["name"])
            name_label.setFixedWidth(100)
            name_label.setStyleSheet("color:#CBD5E1;font-size:12px;")

            # Прогресс-бар
            bar = QProgressBar()
            bar.setValue(percent)
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setStyleSheet(
                f"QProgressBar{{background:#1A1F2E;border-radius:3px;}}"
                f"QProgressBar::chunk{{background:{row['color']};border-radius:3px;}}"
            )

            # Процент
            pct_label = QLabel(f"{percent}%")
            pct_label.setFixedWidth(34)
            pct_label.setAlignment(Qt.AlignRight)
            pct_label.setStyleSheet("color:#475569;font-size:11px;")

            layout.addWidget(dot)
            layout.addWidget(name_label)
            layout.addWidget(bar)
            layout.addWidget(pct_label)
            self.cat_layout.addWidget(frame)

    def _refresh_today_table(self) -> None:
        """Загружает задачи на сегодня и заполняет таблицу на Dashboard."""
        tasks = self.db.get_tasks_today()
        self.today_table.setRowCount(len(tasks))

        for row_idx, task in enumerate(tasks):
            # Чекбокс статуса
            self.today_table.setCellWidget(
                row_idx, 0,
                _make_checkbox_cell(
                    task["status"] == "done",
                    lambda state, tid=task["id"]: self._toggle_task_done(tid),
                ),
            )

            # Название
            title_item = QTableWidgetItem(task["title"])
            if task["status"] == "done":
                font = title_item.font()
                font.setStrikeOut(True)
                title_item.setFont(font)
                title_item.setForeground(QColor("#475569"))
            self.today_table.setItem(row_idx, 1, title_item)

            # Приоритет
            pri_item = QTableWidgetItem(
                PRIORITY_LABELS.get(task["priority"], "")
            )
            pri_item.setForeground(
                QColor(PRIORITY_COLORS.get(task["priority"], "#CBD5E1"))
            )
            self.today_table.setItem(row_idx, 2, pri_item)

    # ── Обновление списка задач ───────────────────────────────────────────────

    def _refresh_task_list(self, tasks: list | None = None) -> None:
        """
        Сохраняет задачи в кеш и применяет текущие фильтры.

        Args:
            tasks (list | None): список задач для отображения.
                None означает «загрузить все задачи из БД».
        """
        self._all_tasks = list(tasks or self.db.get_all_tasks())
        self._apply_filters()

    def _apply_filters(self) -> None:
        """
        Фильтрует и сортирует кеш задач, затем перерисовывает таблицу.

        Кеш _all_tasks уже содержит нужную выборку для текущего раздела
        (например, только просроченные или только задачи на сегодня).
        Поверх этой выборки применяются пользовательские фильтры из панели.

        Для раздела «Высокий приоритет» фильтр по приоритету заблокирован —
        всегда показываются только задачи с priority == 'high'.
        """
        tasks = list(self._all_tasks)

        # Фильтр по категории (доступен в любом разделе)
        selected_category = self.filter_cat_combo.currentData()
        if selected_category is not None:
            tasks = [t for t in tasks if t["category_id"] == selected_category]

        # Фильтр по приоритету — только если раздел не «Высокий приоритет»
        # (там выборка уже ограничена при загрузке)
        if self._current_view != "high":
            selected_priority = self.filter_pri_combo.currentData()
            if selected_priority:
                tasks = [t for t in tasks if t["priority"] == selected_priority]

        # Текстовый поиск по названию
        query = self.search_edit.text().strip().lower()
        if query:
            tasks = [t for t in tasks if query in t["title"].lower()]

        # Сортировка
        sort_key = self.sort_combo.currentData()
        if sort_key == "priority":
            tasks.sort(key=lambda t: PRIORITY_ORDER.get(t["priority"], 1))
        elif sort_key == "deadline":
            tasks.sort(key=lambda t: t["deadline"] or "9999")
        else:
            tasks.sort(key=lambda t: t["created_at"] or "", reverse=True)

        self.filter_count_label.setText(f"Найдено задач: {len(tasks)}")
        self._fill_task_table(tasks)

    def _fill_task_table(self, tasks: list) -> None:
        """
        Заполняет таблицу задач переданным списком.

        Args:
            tasks (list[sqlite3.Row]): задачи для отображения.
        """
        table = self.task_table
        table.setRowCount(0)           # очищаем старые строки
        table.setRowCount(len(tasks))  # резервируем нужное количество

        today = date.today().isoformat()

        for row_idx, task in enumerate(tasks):
            is_done = task["status"] == "done"

            # Чекбокс (столбец 0)
            table.setCellWidget(
                row_idx, 0,
                _make_checkbox_cell(
                    is_done,
                    lambda state, tid=task["id"]: self._toggle_task_done(tid),
                ),
            )

            # Название (столбец 1)
            title_item = QTableWidgetItem(task["title"])
            if is_done:
                font = title_item.font()
                font.setStrikeOut(True)
                title_item.setFont(font)
                title_item.setForeground(QColor("#475569"))
            table.setItem(row_idx, 1, title_item)

            # Категория (столбец 2)
            cat_item = QTableWidgetItem(task["cat_name"] or "—")
            if task["cat_color"]:
                cat_item.setForeground(QColor(task["cat_color"]))
            table.setItem(row_idx, 2, cat_item)

            # Приоритет (столбец 3)
            pri_item = QTableWidgetItem(
                PRIORITY_LABELS.get(task["priority"], "")
            )
            pri_item.setForeground(
                QColor(PRIORITY_COLORS.get(task["priority"], "#CBD5E1"))
            )
            table.setItem(row_idx, 3, pri_item)

            # Дедлайн (столбец 4) с цветовой индикацией
            deadline = task["deadline"]
            if not deadline:
                dl_item = QTableWidgetItem("—")
            elif deadline < today and not is_done:
                dl_item = QTableWidgetItem(f"⚠  {deadline}")
                dl_item.setForeground(QColor("#EF4444"))
            elif deadline == today and not is_done:
                dl_item = QTableWidgetItem(f"📅  {deadline}")
                dl_item.setForeground(QColor("#F59E0B"))
            else:
                dl_item = QTableWidgetItem(deadline)
            table.setItem(row_idx, 4, dl_item)

            # Кнопки действий (столбец 5)
            table.setCellWidget(
                row_idx, 5,
                _make_action_cell(
                    task["id"],
                    self._open_edit_dialog,
                    self._delete_task,
                ),
            )

    def _reset_filters(self) -> None:
        """Сбрасывает все фильтры и строку поиска в исходное состояние."""
        self.filter_cat_combo.setCurrentIndex(0)
        self.filter_pri_combo.setCurrentIndex(0)
        self.sort_combo.setCurrentIndex(0)
        self.search_edit.clear()

    # ── Навигация ─────────────────────────────────────────────────────────────

    def _on_nav_changed(self, row: int) -> None:
        """
        Обрабатывает выбор пункта навигации.

        Args:
            row (int): индекс выбранного пункта в QListWidget.
        """
        item = self.nav_list.item(row)
        if item:
            self._switch_view(item.data(Qt.UserRole))

    def _switch_view(self, key: str) -> None:
        """
        Переключает центральный виджет и загружает соответствующие данные.

        Args:
            key (str): идентификатор вида —
                'dashboard', 'all', 'today', 'overdue' или 'high'.
        """
        self._current_view = key
        self.stack.setCurrentIndex(0 if key == "dashboard" else 1)

        if key != "dashboard":
            self._load_tasks_for_view(key)

        # Синхронизируем выделение в навигации
        for i in range(self.nav_list.count()):
            if self.nav_list.item(i).data(Qt.UserRole) == key:
                self.nav_list.setCurrentRow(i)
                break

    def _load_tasks_for_view(self, key: str) -> None:
        """
        Загружает задачи из БД в зависимости от текущего раздела.

        Args:
            key (str): идентификатор раздела ('all', 'today', 'overdue', 'high').
        """
        if key == "all":
            tasks = self.db.get_all_tasks()
        elif key == "today":
            tasks = self.db.get_tasks_today()
        elif key == "overdue":
            tasks = self.db.get_overdue_tasks()
        elif key == "high":
            tasks = [t for t in self.db.get_all_tasks() if t["priority"] == "high"]
        else:
            tasks = self.db.get_all_tasks()
        self._refresh_task_list(tasks)

    # ── CRUD действия ─────────────────────────────────────────────────────────

    def _open_create_dialog(self) -> None:
        """Открывает диалог создания новой задачи."""
        dialog = TaskDialog(self.db, parent=self)
        if dialog.exec_():
            self.refresh()
            self.status_bar.showMessage("✓  Задача создана", 3000)

    def _open_edit_dialog(self) -> None:
        """Открывает диалог редактирования задачи, id которой передан через свойство кнопки."""
        task_id = self.sender().property("task_id")
        task = next(
            (t for t in self.db.get_all_tasks() if t["id"] == task_id), None
        )
        if not task:
            return
        dialog = TaskDialog(self.db, task=task, parent=self)
        if dialog.exec_():
            self.refresh()
            self.status_bar.showMessage("✓  Задача обновлена", 3000)

    def _delete_task(self) -> None:
        """Запрашивает подтверждение и удаляет задачу по id из свойства кнопки."""
        task_id = self.sender().property("task_id")
        reply = QMessageBox.question(
            self,
            "Удалить задачу",
            "Удалить задачу? Действие необратимо.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_task(task_id)
            self.refresh()
            self.status_bar.showMessage("Задача удалена", 3000)

    def _toggle_task_done(self, task_id: int) -> None:
        """
        Переключает статус задачи (выполнена / не выполнена) и обновляет UI.

        Args:
            task_id (int): идентификатор задачи.
        """
        self.db.toggle_status(task_id)
        self.refresh()

    def _open_categories_dialog(self) -> None:
        """Открывает диалог управления категориями и обновляет фильтры после закрытия."""
        CategoryDialog(self.db, parent=self).exec_()
        self._reload_category_filter()
        self.refresh()

    # ── Вспомогательные методы ────────────────────────────────────────────────

    def _on_search_changed(self) -> None:
        """
        Обрабатывает ввод в строку поиска.

        При поиске переключается на раздел «Все задачи» и ищет по всему списку.
        """
        query = self.search_edit.text().strip()

        if query:
            # Поиск всегда работает по всем задачам — переключаем в «Все»
            if self._current_view != "all":
                self._current_view = "all"
                self.stack.setCurrentIndex(1)
                for i in range(self.nav_list.count()):
                    if self.nav_list.item(i).data(Qt.UserRole) == "all":
                        self.nav_list.setCurrentRow(i)
                        break
                # Загружаем все задачи в кеш если ещё не загружены
                if not self._all_tasks:
                    self._all_tasks = list(self.db.get_all_tasks())
            elif not self._all_tasks:
                self._all_tasks = list(self.db.get_all_tasks())

        if self.stack.currentIndex() == 1:
            self._apply_filters()

    def _reload_category_filter(self) -> None:
        """Перезагружает список категорий в выпадающем фильтре."""
        self.filter_cat_combo.blockSignals(True)
        self.filter_cat_combo.clear()
        self.filter_cat_combo.addItem("Все категории", None)
        for cat in self.db.get_all_categories():
            self.filter_cat_combo.addItem(cat["name"], cat["id"])
        self.filter_cat_combo.blockSignals(False)

    def _on_timer_tick(self) -> None:
        """Инкрементирует счётчик таймера и отображает время в строке состояния."""
        self._timer_secs += 1
        hours, remainder = divmod(self._timer_secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.status_bar.showMessage(f"⏱  {hours:02}:{minutes:02}:{seconds:02}")

    def refresh(self) -> None:
        """
        Полностью обновляет все виджеты окна из базы данных.

        Перезагружает именно ту выборку задач, которая соответствует
        текущему активному разделу навигации.
        """
        self._reload_category_filter()
        self._refresh_dashboard()

        # Если список задач виден — перезагружаем именно текущий раздел,
        # а не все задачи подряд
        if self.stack.currentIndex() == 1:
            self._load_tasks_for_view(self._current_view)

        stats = self.db.get_stats()
        self.status_bar.showMessage(
            f"  ✓ Выполнено: {stats['done']}/{stats['total']}    "
            f"⚠ Просрочено: {stats['overdue']}    "
            f"📅 На сегодня: {stats['today']}"
        )
