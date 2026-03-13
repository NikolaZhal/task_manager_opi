from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QDockWidget, QListWidget, QListWidgetItem, QGroupBox,
    QLabel, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QToolBar, QLineEdit, QComboBox,
    QCheckBox, QStatusBar, QMessageBox, QSizePolicy,
    QStackedWidget, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QColor, QFont
from datetime import date

from task_dialog import TaskDialog
from category_dialog import CategoryDialog

PRI_LABEL = {"low": "↓  Низкий", "medium": "→  Средний", "high": "↑  Высокий"}
PRI_ORDER = {"high": 0, "medium": 1, "low": 2}
PRI_COLOR = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444"}

QSS = """
QMainWindow, QWidget {
    background-color: #0F1117;
    color: #E2E8F0;
    font-family: 'Segoe UI', Tahoma, sans-serif;
    font-size: 13px;
}
QDockWidget { background: #0F1117; border: none; }
QDockWidget::title {
    background: #1A1D2E;
    padding: 10px 14px;
    font-size: 11px; font-weight: 600;
    letter-spacing: 1.5px; color: #64748B;
    border-bottom: 1px solid #2D3748;
}
QListWidget { background: #1A1D2E; border: none; outline: none; padding: 8px 0; }
QListWidget::item {
    padding: 11px 20px; margin: 2px 8px;
    border-radius: 8px; color: #94A3B8; font-size: 13px;
}
QListWidget::item:hover { background: #252840; color: #CBD5E1; }
QListWidget::item:selected {
    background: #3B4BDB; color: #FFFFFF; font-weight: 600;
}
QToolBar {
    background: #1A1D2E; border: none;
    border-bottom: 1px solid #2D3748; padding: 6px 12px; spacing: 8px;
}
QToolBar::separator { background: #2D3748; width: 1px; margin: 6px 4px; }
QMenuBar { background: #1A1D2E; color: #94A3B8; border-bottom: 1px solid #2D3748; padding: 2px 8px; }
QMenuBar::item:selected { background: #252840; border-radius: 4px; color: #E2E8F0; }
QMenu { background: #1E2130; border: 1px solid #2D3748; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 8px 20px; border-radius: 4px; color: #CBD5E1; }
QMenu::item:selected { background: #3B4BDB; color: white; }
QPushButton {
    background: #252840; color: #CBD5E1;
    border: 1px solid #334155; border-radius: 7px;
    padding: 7px 16px; font-size: 13px;
}
QPushButton:hover { background: #2D3254; border-color: #4B5B8C; color: #F1F5F9; }
QPushButton:pressed { background: #1E2340; }
QPushButton#primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3B4BDB, stop:1 #6366F1);
    color: white; border: none; font-weight: 600; padding: 8px 20px;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #4C5EE8, stop:1 #7577F5);
}
QPushButton#danger { color: #EF4444; border-color: #3D1515; background: #1A1117; }
QPushButton#danger:hover { background: #3D1515; border-color: #EF4444; }
QPushButton#small { padding: 4px 10px; font-size: 12px; border-radius: 5px; }
QLineEdit, QTextEdit, QDoubleSpinBox, QSpinBox {
    background: #1E2130; color: #E2E8F0;
    border: 1px solid #2D3748; border-radius: 7px;
    padding: 8px 12px; font-size: 13px;
    selection-background-color: #3B4BDB;
}
QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {
    border: 1px solid #3B4BDB; background: #1A1D2E;
}
QComboBox {
    background: #1E2130; color: #CBD5E1;
    border: 1px solid #2D3748; border-radius: 7px;
    padding: 7px 12px; min-width: 130px;
}
QComboBox:hover { border-color: #4B5B8C; }
QComboBox:focus { border-color: #3B4BDB; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #1E2130; border: 1px solid #3B4BDB;
    border-radius: 7px; color: #CBD5E1;
    selection-background-color: #3B4BDB; padding: 4px;
}
QDateEdit {
    background: #1E2130; color: #CBD5E1;
    border: 1px solid #2D3748; border-radius: 7px; padding: 7px 12px;
}
QDateEdit:focus { border-color: #3B4BDB; }
QTableWidget {
    background: #0F1117; border: none;
    gridline-color: #1E2130; outline: none;
    alternate-background-color: #13161F;
}
QTableWidget::item { padding: 10px 12px; color: #CBD5E1; }
QTableWidget::item:selected { background: #1E2D5E; color: #E2E8F0; }
QTableWidget::item:hover { background: #1A2040; }
QHeaderView::section {
    background: #1A1D2E; color: #64748B;
    font-size: 11px; font-weight: 600; letter-spacing: 0.8px;
    padding: 10px 12px; border: none;
    border-bottom: 2px solid #2D3748;
    border-right: 1px solid #2D3748;
}
QGroupBox {
    background: #13161F; border: 1px solid #1E2130;
    border-radius: 12px; margin-top: 18px;
    padding: 16px 14px 10px; color: #64748B;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 14px; top: -1px;
    padding: 0 6px; color: #94A3B8;
    font-size: 11px; letter-spacing: 1px;
    background: #0F1117;
}
QProgressBar {
    background: #1E2130; border: none; border-radius: 6px; height: 8px;
    color: transparent; text-align: center; font-size: 10px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3B4BDB, stop:1 #6366F1);
    border-radius: 6px;
}
QScrollBar:vertical { background: #0F1117; width: 6px; border: none; border-radius: 3px; }
QScrollBar::handle:vertical { background: #2D3748; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #4B5B8C; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 4px;
    border: 2px solid #334155; background: transparent;
}
QCheckBox::indicator:hover { border-color: #3B4BDB; }
QCheckBox::indicator:checked { background: #3B4BDB; border-color: #3B4BDB; }
QStatusBar {
    background: #1A1D2E; color: #4A5568;
    border-top: 1px solid #2D3748; font-size: 12px; padding: 2px 12px;
}
QDialog { background: #13161F; }
QRadioButton { color: #94A3B8; spacing: 8px; }
QRadioButton::indicator {
    width: 16px; height: 16px; border-radius: 8px;
    border: 2px solid #334155; background: transparent;
}
QRadioButton::indicator:checked { background: #3B4BDB; border-color: #3B4BDB; }
QRadioButton:checked { color: #E2E8F0; font-weight: 600; }
QScrollArea { border: none; background: transparent; }
QMessageBox { background: #13161F; }
QMessageBox QPushButton { min-width: 80px; }
"""


class StatCard(QFrame):
    def __init__(self, icon, title, accent="#3B4BDB"):
        super().__init__()
        self.setFixedHeight(88)
        self.setStyleSheet(f"""
            QFrame {{ background: #13161F; border: 1px solid #1E2130;
                      border-left: 3px solid {accent}; border-radius: 10px; }}
            QLabel {{ border: none; background: transparent; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(3)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"color: {accent}; font-size: 16px;")
        top.addWidget(icon_lbl)
        top.addStretch()
        lay.addLayout(top)

        self.val_lbl = QLabel("0")
        self.val_lbl.setStyleSheet(f"color: {accent}; font-size: 26px; font-weight: 700;")
        lay.addWidget(self.val_lbl)

        t = QLabel(title)
        t.setStyleSheet("color: #4A5568; font-size: 11px; letter-spacing: 0.3px;")
        lay.addWidget(t)

    def set_value(self, v):
        self.val_lbl.setText(str(v))


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Task Manager")
        self.setMinimumSize(1080, 660)
        self.setStyleSheet(QSS)

        self._timer = QTimer(self)
        self._timer_secs = 0
        self._timer.timeout.connect(self._tick_timer)
        self._all_tasks = []

        self._build_menu()
        self._build_toolbar()
        self._build_dock()
        self._build_central()
        self._build_statusbar()
        self.refresh()

    def _build_menu(self):
        mb = self.menuBar()
        mb.addMenu("Файл").addAction("Выход", self.close)
        mb.addMenu("Задачи").addAction("Новая задача", self._open_create_dialog)
        mb.addMenu("Настройки").addAction("Управление категориями", self._open_categories)

    def _build_toolbar(self):
        tb = QToolBar(self)
        tb.setMovable(False)
        self.addToolBar(tb)

        new_btn = QPushButton("  +  Новая задача")
        new_btn.setObjectName("primary")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._open_create_dialog)
        tb.addWidget(new_btn)
        tb.addSeparator()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("  🔍  Поиск...")
        self.search_edit.setFixedWidth(240)
        self.search_edit.textChanged.connect(self._on_search)
        tb.addWidget(self.search_edit)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        cat_btn = QPushButton("⚙  Категории")
        cat_btn.setObjectName("small")
        cat_btn.clicked.connect(self._open_categories)
        tb.addWidget(cat_btn)

    def _build_dock(self):
        dock = QDockWidget("Навигация", self)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock.setMinimumWidth(200)
        self.nav_list = QListWidget()
        for label, key in [
            ("🏠   Главная",            "dashboard"),
            ("📋   Все задачи",         "all"),
            ("📅   На сегодня",         "today"),
            ("⚠   Просроченные",       "overdue"),
            ("⬆   Высокий приоритет",  "high"),
        ]:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.nav_list.addItem(item)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav)
        dock.setWidget(self.nav_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _build_central(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.stack.addWidget(self._build_dashboard())
        self.stack.addWidget(self._build_task_list())

    # ── Dashboard ─────────────────────────────────────────
    def _build_dashboard(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        w = QWidget()
        w.setStyleSheet("background: #0F1117;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(18)

        hdr = QLabel("Dashboard")
        hdr.setStyleSheet("font-size: 22px; font-weight: 700; color: #E2E8F0;")
        lay.addWidget(hdr)

        # Stat cards
        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_total   = StatCard("📋", "Всего задач",  "#6366F1")
        self.card_done    = StatCard("✅", "Выполнено",    "#10B981")
        self.card_overdue = StatCard("⚠",  "Просрочено",  "#EF4444")
        self.card_today   = StatCard("📅", "На сегодня",   "#F59E0B")
        for c in (self.card_total, self.card_done, self.card_overdue, self.card_today):
            cards.addWidget(c)
        lay.addLayout(cards)

        # Overall progress
        pf = QFrame()
        pf.setStyleSheet("QFrame { background:#13161F; border:1px solid #1E2130; border-radius:12px; } QLabel { border:none; background:transparent; }")
        pl = QVBoxLayout(pf)
        pl.setContentsMargins(16, 12, 16, 12)
        pr_row = QHBoxLayout()
        pr_lbl = QLabel("Общий прогресс")
        pr_lbl.setStyleSheet("color:#94A3B8; font-weight:600;")
        self.prog_pct_lbl = QLabel("0%")
        self.prog_pct_lbl.setStyleSheet("color:#6366F1; font-weight:700;")
        pr_row.addWidget(pr_lbl); pr_row.addStretch(); pr_row.addWidget(self.prog_pct_lbl)
        self.progress_all = QProgressBar()
        self.progress_all.setFixedHeight(10)
        self.progress_all.setTextVisible(False)
        pl.addLayout(pr_row); pl.addWidget(self.progress_all)
        lay.addWidget(pf)

        # Bottom: categories + today
        bot = QHBoxLayout(); bot.setSpacing(16)

        cat_box = QGroupBox("По категориям")
        self.cat_layout = QVBoxLayout(cat_box)
        self.cat_layout.setSpacing(10)
        bot.addWidget(cat_box, 1)

        today_box = QGroupBox("Задачи на сегодня")
        tv = QVBoxLayout(today_box)
        self.today_table = QTableWidget(0, 3)
        self.today_table.setHorizontalHeaderLabels(["", "Задача", "Приоритет"])
        self.today_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.today_table.setColumnWidth(0, 36); self.today_table.setColumnWidth(2, 110)
        self.today_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.today_table.verticalHeader().setVisible(False)
        self.today_table.setAlternatingRowColors(True)
        self.today_table.setShowGrid(False)
        tv.addWidget(self.today_table)
        go_btn = QPushButton("Все задачи  →")
        go_btn.setObjectName("small"); go_btn.clicked.connect(lambda: self._switch_view("all"))
        tv.addWidget(go_btn, alignment=Qt.AlignRight)
        bot.addWidget(today_box, 2)
        lay.addLayout(bot); lay.addStretch()
        scroll.setWidget(w)
        return scroll

    def _refresh_dashboard(self):
        stats = self.db.get_stats()
        total, done, overdue, today_c = stats["total"], stats["done"], stats["overdue"], stats["today"]
        self.card_total.set_value(total)
        self.card_done.set_value(done)
        self.card_overdue.set_value(overdue)
        self.card_today.set_value(today_c)
        pct = int(done / total * 100) if total else 0
        self.progress_all.setValue(pct)
        self.prog_pct_lbl.setText(f"{pct}%")

        for i in reversed(range(self.cat_layout.count())):
            w = self.cat_layout.itemAt(i).widget()
            if w: w.deleteLater()

        for row in stats["cat_stats"]:
            t, d = row["total"], row["done"] or 0
            p = int(d / t * 100) if t else 0
            frame = QFrame()
            frame.setStyleSheet("QFrame{background:transparent;border:none;} QLabel{border:none;background:transparent;}")
            h = QHBoxLayout(frame); h.setContentsMargins(0,0,0,0); h.setSpacing(10)
            dot = QLabel("●"); dot.setStyleSheet(f"color:{row['color']};font-size:9px;"); dot.setFixedWidth(12)
            nm = QLabel(row["name"]); nm.setFixedWidth(100); nm.setStyleSheet("color:#CBD5E1;font-size:12px;")
            bar = QProgressBar(); bar.setValue(p); bar.setFixedHeight(7); bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar{{background:#1E2130;border-radius:4px;}} QProgressBar::chunk{{background:{row['color']};border-radius:4px;}}")
            pct_l = QLabel(f"{p}%"); pct_l.setFixedWidth(36); pct_l.setAlignment(Qt.AlignRight)
            pct_l.setStyleSheet("color:#4A5568;font-size:11px;")
            h.addWidget(dot); h.addWidget(nm); h.addWidget(bar); h.addWidget(pct_l)
            self.cat_layout.addWidget(frame)

        today_tasks = self.db.get_tasks_today()
        self.today_table.setRowCount(len(today_tasks))
        for r, t in enumerate(today_tasks):
            cb = QCheckBox(); cb.setChecked(t["status"] == "done")
            cb.stateChanged.connect(lambda s, tid=t["id"]: self._toggle_done(tid))
            cw = QWidget(); cl = QHBoxLayout(cw); cl.setContentsMargins(6,0,0,0); cl.addWidget(cb)
            self.today_table.setCellWidget(r, 0, cw)
            ti = QTableWidgetItem(t["title"])
            if t["status"] == "done":
                f = ti.font(); f.setStrikeOut(True); ti.setFont(f); ti.setForeground(QColor("#4A5568"))
            self.today_table.setItem(r, 1, ti)
            pi = QTableWidgetItem(PRI_LABEL.get(t["priority"], ""))
            pi.setForeground(QColor(PRI_COLOR.get(t["priority"], "#CBD5E1")))
            self.today_table.setItem(r, 2, pi)

    # ── Task list ─────────────────────────────────────────
    def _build_task_list(self):
        w = QWidget(); w.setStyleSheet("background:#0F1117;")
        lay = QVBoxLayout(w); lay.setContentsMargins(24,20,24,16); lay.setSpacing(14)

        hdr = QLabel("Список задач")
        hdr.setStyleSheet("font-size:22px;font-weight:700;color:#E2E8F0;")
        lay.addWidget(hdr)

        ff = QFrame()
        ff.setStyleSheet("QFrame{background:#13161F;border:1px solid #1E2130;border-radius:10px;} QLabel{border:none;background:transparent;}")
        fh = QHBoxLayout(ff); fh.setContentsMargins(14,10,14,10); fh.setSpacing(10)

        self.filter_cat = QComboBox(); self.filter_cat.addItem("Все категории", None)
        self.filter_pri = QComboBox()
        for lbl, val in [("Все приоритеты", None), ("↑  Высокий","high"), ("→  Средний","medium"), ("↓  Низкий","low")]:
            self.filter_pri.addItem(lbl, val)
        self.sort_combo = QComboBox()
        for lbl, val in [("По дедлайну","deadline"),("По приоритету","priority"),("По дате","created_at")]:
            self.sort_combo.addItem(lbl, val)

        reset_btn = QPushButton("Сбросить"); reset_btn.setObjectName("small")
        reset_btn.clicked.connect(self._reset_filters)

        for lbl, widget in [("Категория:", self.filter_cat), ("Приоритет:", self.filter_pri), ("Сортировка:", self.sort_combo)]:
            l = QLabel(lbl); l.setStyleSheet("color:#64748B;font-size:12px;")
            fh.addWidget(l); fh.addWidget(widget)
        fh.addStretch(); fh.addWidget(reset_btn)
        lay.addWidget(ff)

        self.filter_status_lbl = QLabel("")
        self.filter_status_lbl.setStyleSheet("color:#4A5568;font-size:12px;padding-left:2px;")
        lay.addWidget(self.filter_status_lbl)

        self.task_table = QTableWidget(0, 6)
        self.task_table.setHorizontalHeaderLabels(["", "Название", "Категория", "Приоритет", "Дедлайн", ""])
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.task_table.setColumnWidth(0, 44); self.task_table.setColumnWidth(2, 120)
        self.task_table.setColumnWidth(3, 120); self.task_table.setColumnWidth(4, 105)
        self.task_table.setColumnWidth(5, 80)
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setShowGrid(False)
        self.task_table.verticalHeader().setDefaultSectionSize(46)
        lay.addWidget(self.task_table)

        self.filter_cat.currentIndexChanged.connect(self._apply_filters)
        self.filter_pri.currentIndexChanged.connect(self._apply_filters)
        self.sort_combo.currentIndexChanged.connect(self._apply_filters)
        return w

    def _refresh_task_list(self, tasks=None):
        self._all_tasks = list(tasks or self.db.get_all_tasks())
        self._apply_filters()

    def _apply_filters(self):
        tasks = list(self._all_tasks)
        cat_id = self.filter_cat.currentData()
        if cat_id is not None: tasks = [t for t in tasks if t["category_id"] == cat_id]
        pri = self.filter_pri.currentData()
        if pri: tasks = [t for t in tasks if t["priority"] == pri]
        q = self.search_edit.text().strip().lower()
        if q: tasks = [t for t in tasks if q in t["title"].lower()]
        sf = self.sort_combo.currentData()
        if sf == "priority": tasks.sort(key=lambda t: PRI_ORDER.get(t["priority"], 1))
        elif sf == "deadline": tasks.sort(key=lambda t: (t["deadline"] or "9999"))
        else: tasks.sort(key=lambda t: t["created_at"] or "", reverse=True)
        self.filter_status_lbl.setText(f"Найдено задач: {len(tasks)}")
        self._fill_task_table(tasks)

    def _fill_task_table(self, tasks):
        self.task_table.setRowCount(len(tasks))
        today = date.today().isoformat()
        for r, task in enumerate(tasks):
            cb = QCheckBox(); cb.setChecked(task["status"] == "done")
            cb.stateChanged.connect(lambda s, tid=task["id"]: self._toggle_done(tid))
            cw = QWidget(); cl = QHBoxLayout(cw); cl.setContentsMargins(12,0,0,0); cl.addWidget(cb)
            self.task_table.setCellWidget(r, 0, cw)

            ti = QTableWidgetItem(task["title"])
            if task["status"] == "done":
                f = ti.font(); f.setStrikeOut(True); ti.setFont(f); ti.setForeground(QColor("#4A5568"))
            self.task_table.setItem(r, 1, ti)

            cat_item = QTableWidgetItem(f"  {task['cat_name'] or '—'}  ")
            if task["cat_color"]: cat_item.setForeground(QColor(task["cat_color"]))
            self.task_table.setItem(r, 2, cat_item)

            pri_item = QTableWidgetItem(PRI_LABEL.get(task["priority"], ""))
            pri_item.setForeground(QColor(PRI_COLOR.get(task["priority"], "#CBD5E1")))
            self.task_table.setItem(r, 3, pri_item)

            dl = task["deadline"] or "—"
            dl_item = QTableWidgetItem(dl)
            if task["deadline"] and task["deadline"] < today and task["status"] == "pending":
                dl_item.setForeground(QColor("#EF4444")); dl_item.setText(f"⚠  {dl}")
            elif task["deadline"] == today:
                dl_item.setForeground(QColor("#F59E0B"))
            self.task_table.setItem(r, 4, dl_item)

            aw = QWidget(); ah = QHBoxLayout(aw); ah.setContentsMargins(4,4,4,4); ah.setSpacing(4)
            eb = QPushButton("✎"); eb.setObjectName("small"); eb.setFixedSize(30, 30)
            eb.setCursor(Qt.PointingHandCursor); eb.setProperty("task_id", task["id"])
            eb.clicked.connect(self._open_edit_dialog)
            db_ = QPushButton("✕"); db_.setObjectName("danger"); db_.setFixedSize(30, 30)
            db_.setCursor(Qt.PointingHandCursor); db_.setProperty("task_id", task["id"])
            db_.clicked.connect(self._delete_task)
            ah.addWidget(eb); ah.addWidget(db_)
            self.task_table.setCellWidget(r, 5, aw)

    def _reset_filters(self):
        self.filter_cat.setCurrentIndex(0)
        self.filter_pri.setCurrentIndex(0)
        self.sort_combo.setCurrentIndex(0)
        self.search_edit.clear()

    def _build_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _on_nav(self, row):
        item = self.nav_list.item(row)
        if item: self._switch_view(item.data(Qt.UserRole))

    def _switch_view(self, key):
        self.stack.setCurrentIndex(0 if key == "dashboard" else 1)
        if key != "dashboard":
            if key == "all": self._refresh_task_list()
            elif key == "today": self._refresh_task_list(self.db.get_tasks_today())
            elif key == "overdue": self._refresh_task_list(self.db.get_overdue_tasks())
            elif key == "high":
                self._refresh_task_list([t for t in self.db.get_all_tasks() if t["priority"] == "high"])
        for i in range(self.nav_list.count()):
            if self.nav_list.item(i).data(Qt.UserRole) == key:
                self.nav_list.setCurrentRow(i); break

    def _open_create_dialog(self):
        dlg = TaskDialog(self.db, parent=self)
        if dlg.exec_(): self.refresh(); self.status_bar.showMessage("✓  Задача создана", 3000)

    def _open_edit_dialog(self):
        task_id = self.sender().property("task_id")
        task = next((t for t in self.db.get_all_tasks() if t["id"] == task_id), None)
        if not task: return
        dlg = TaskDialog(self.db, task=task, parent=self)
        if dlg.exec_(): self.refresh(); self.status_bar.showMessage("✓  Задача обновлена", 3000)

    def _delete_task(self):
        task_id = self.sender().property("task_id")
        if QMessageBox.question(self, "Удалить задачу", "Удалить задачу? Действие необратимо.",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_task(task_id)
            self.refresh(); self.status_bar.showMessage("Задача удалена", 3000)

    def _toggle_done(self, task_id):
        self.db.toggle_status(task_id); self.refresh()

    def _open_categories(self):
        CategoryDialog(self.db, parent=self).exec_()
        self._reload_cat_filter(); self.refresh()

    def _on_search(self):
        if self.stack.currentIndex() == 1: self._apply_filters()

    def _reload_cat_filter(self):
        self.filter_cat.blockSignals(True)
        self.filter_cat.clear()
        self.filter_cat.addItem("Все категории", None)
        for cat in self.db.get_all_categories():
            self.filter_cat.addItem(cat["name"], cat["id"])
        self.filter_cat.blockSignals(False)

    def _tick_timer(self):
        self._timer_secs += 1
        h, rem = divmod(self._timer_secs, 3600); m, s = divmod(rem, 60)
        self.status_bar.showMessage(f"⏱  {h:02}:{m:02}:{s:02}")

    def refresh(self):
        self._reload_cat_filter()
        self._refresh_dashboard()
        if self.stack.currentIndex() == 1: self._refresh_task_list()
        s = self.db.get_stats()
        self.status_bar.showMessage(
            f"  ✓ Выполнено: {s['done']}/{s['total']}    "
            f"⚠ Просрочено: {s['overdue']}    📅 На сегодня: {s['today']}"
        )
