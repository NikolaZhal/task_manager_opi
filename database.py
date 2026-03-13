"""
Модуль работы с базой данных SQLite.

Содержит класс DatabaseManager — единственную точку доступа
ко всем операциям хранения данных приложения.
"""

import sqlite3
from datetime import date


class DatabaseManager:
    """
    Менеджер базы данных SQLite для системы управления задачами.

    Обеспечивает CRUD-операции над задачами и категориями,
    а также вычисление сводной статистики.

    Attributes:
        conn (sqlite3.Connection): активное соединение с БД.
    """

    # Максимально допустимое количество категорий
    MAX_CATEGORIES = 9

    def __init__(self, db_path: str) -> None:
        """
        Инициализирует соединение с БД и создаёт таблицы при первом запуске.

        Args:
            db_path (str): путь к файлу базы данных (.db).
        """
        # Открываем соединение; row_factory позволяет обращаться к столбцам по имени
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()
        self._seed_default_categories()

    # ── Инициализация схемы ───────────────────────────────────────────────────

    def _create_tables(self) -> None:
        """Создаёт таблицы categories и tasks, если они ещё не существуют."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL UNIQUE,
                color      TEXT    NOT NULL DEFAULT '#4A90D9'
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                title            TEXT    NOT NULL,
                description      TEXT    DEFAULT '',
                category_id      INTEGER,
                priority         TEXT    DEFAULT 'medium',
                status           TEXT    DEFAULT 'pending',
                deadline         TEXT,
                estimated_hours  REAL    DEFAULT 0,
                tracked_seconds  INTEGER DEFAULT 0,
                created_at       TEXT    DEFAULT (date('now')),
                FOREIGN KEY (category_id)
                    REFERENCES categories(id) ON DELETE SET NULL
            );
        """)
        self.conn.commit()

    def _seed_default_categories(self) -> None:
        """Добавляет три стандартные категории при первом запуске приложения."""
        defaults = [
            ("Работа",  "#4A90D9"),
            ("Личное",  "#2ECC71"),
            ("Учёба",   "#F39C12"),
        ]
        for name, color in defaults:
            try:
                self.conn.execute(
                    "INSERT INTO categories (name, color) VALUES (?, ?)",
                    (name, color),
                )
            except sqlite3.IntegrityError:
                # Категория уже существует — пропускаем
                pass
        self.conn.commit()

    # ── Задачи: чтение ────────────────────────────────────────────────────────

    def get_all_tasks(self) -> list:
        """
        Возвращает все задачи с данными их категорий.

        Returns:
            list[sqlite3.Row]: строки таблицы tasks + cat_name, cat_color.
        """
        return self.conn.execute(
            "SELECT t.*, c.name AS cat_name, c.color AS cat_color "
            "FROM tasks t LEFT JOIN categories c ON t.category_id = c.id "
            "ORDER BY t.created_at DESC"
        ).fetchall()

    def get_tasks_today(self) -> list:
        """
        Возвращает незавершённые задачи с дедлайном на сегодня.

        Returns:
            list[sqlite3.Row]: задачи, у которых deadline == date.today().
        """
        today = date.today().isoformat()
        return self.conn.execute(
            "SELECT t.*, c.name AS cat_name, c.color AS cat_color "
            "FROM tasks t LEFT JOIN categories c ON t.category_id = c.id "
            "WHERE t.deadline = ? AND t.status = 'pending' "
            "ORDER BY t.priority",
            (today,),
        ).fetchall()

    def get_overdue_tasks(self) -> list:
        """
        Возвращает незавершённые задачи с истёкшим сроком выполнения.

        Returns:
            list[sqlite3.Row]: задачи, у которых deadline < date.today().
        """
        today = date.today().isoformat()
        return self.conn.execute(
            "SELECT t.*, c.name AS cat_name, c.color AS cat_color "
            "FROM tasks t LEFT JOIN categories c ON t.category_id = c.id "
            "WHERE t.deadline < ? AND t.status = 'pending' "
            "ORDER BY t.deadline",
            (today,),
        ).fetchall()

    # ── Задачи: запись ────────────────────────────────────────────────────────

    def create_task(
        self,
        title: str,
        description: str,
        category_id: int | None,
        priority: str,
        deadline: str | None,
        estimated_hours: float,
    ) -> int:
        """
        Создаёт новую задачу в базе данных.

        Args:
            title (str): название задачи (обязательное поле).
            description (str): подробное описание.
            category_id (int | None): идентификатор категории или None.
            priority (str): приоритет — 'low', 'medium' или 'high'.
            deadline (str | None): дата дедлайна в формате 'YYYY-MM-DD' или None.
            estimated_hours (float): оценка времени выполнения в часах.

        Returns:
            int: идентификатор созданной записи (lastrowid).
        """
        cursor = self.conn.execute(
            "INSERT INTO tasks "
            "(title, description, category_id, priority, deadline, estimated_hours) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, category_id, priority, deadline, estimated_hours),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_task(
        self,
        task_id: int,
        title: str,
        description: str,
        category_id: int | None,
        priority: str,
        deadline: str | None,
        estimated_hours: float,
    ) -> None:
        """
        Обновляет основные поля существующей задачи.

        Args:
            task_id (int): идентификатор обновляемой задачи.
            title (str): новое название.
            description (str): новое описание.
            category_id (int | None): новая категория.
            priority (str): новый приоритет.
            deadline (str | None): новый дедлайн.
            estimated_hours (float): новая оценка времени.
        """
        self.conn.execute(
            "UPDATE tasks "
            "SET title=?, description=?, category_id=?, priority=?, "
            "    deadline=?, estimated_hours=? "
            "WHERE id=?",
            (title, description, category_id, priority,
             deadline, estimated_hours, task_id),
        )
        self.conn.commit()

    def toggle_status(self, task_id: int) -> None:
        """
        Переключает статус задачи между 'pending' и 'done'.

        Args:
            task_id (int): идентификатор задачи.
        """
        row = self.conn.execute(
            "SELECT status FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        new_status = "done" if row["status"] == "pending" else "pending"
        self.conn.execute(
            "UPDATE tasks SET status=? WHERE id=?", (new_status, task_id)
        )
        self.conn.commit()

    def delete_task(self, task_id: int) -> None:
        """
        Удаляет задачу по идентификатору.

        Args:
            task_id (int): идентификатор удаляемой задачи.
        """
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def update_tracked_time(self, task_id: int, seconds: int) -> None:
        """
        Прибавляет указанное количество секунд к счётчику отслеживания времени.

        Args:
            task_id (int): идентификатор задачи.
            seconds (int): количество секунд для добавления.
        """
        self.conn.execute(
            "UPDATE tasks SET tracked_seconds = tracked_seconds + ? WHERE id=?",
            (seconds, task_id),
        )
        self.conn.commit()

    # ── Категории ─────────────────────────────────────────────────────────────

    def get_all_categories(self) -> list:
        """
        Возвращает все категории, отсортированные по имени.

        Returns:
            list[sqlite3.Row]: строки таблицы categories.
        """
        return self.conn.execute(
            "SELECT * FROM categories ORDER BY name"
        ).fetchall()

    def create_category(self, name: str, color: str) -> int:
        """
        Создаёт новую категорию.

        Args:
            name (str): уникальное название категории.
            color (str): цвет в формате HEX (#RRGGBB).

        Returns:
            int: идентификатор созданной записи.

        Raises:
            sqlite3.IntegrityError: если категория с таким именем уже существует.
        """
        cursor = self.conn.execute(
            "INSERT INTO categories (name, color) VALUES (?, ?)", (name, color)
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_category(self, cat_id: int, name: str, color: str) -> None:
        """
        Обновляет название и цвет категории.

        Args:
            cat_id (int): идентификатор категории.
            name (str): новое название.
            color (str): новый цвет в формате HEX.
        """
        self.conn.execute(
            "UPDATE categories SET name=?, color=? WHERE id=?",
            (name, color, cat_id),
        )
        self.conn.commit()

    def delete_category(self, cat_id: int) -> None:
        """
        Удаляет категорию. Связанные задачи получают category_id = NULL.

        Args:
            cat_id (int): идентификатор удаляемой категории.
        """
        self.conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
        self.conn.commit()

    # ── Статистика ────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """
        Вычисляет сводную статистику по задачам.

        Returns:
            dict: словарь с ключами:
                - total (int): общее число задач;
                - done (int): число выполненных задач;
                - overdue (int): число просроченных незавершённых задач;
                - today (int): число задач с дедлайном сегодня;
                - cat_stats (list[sqlite3.Row]): статистика по категориям
                  (поля: id, name, color, total, done).
        """
        total = self.conn.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]

        done = self.conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status='done'"
        ).fetchone()[0]

        overdue = self.conn.execute(
            "SELECT COUNT(*) FROM tasks "
            "WHERE deadline < date('now') AND status='pending'"
        ).fetchone()[0]

        today_count = self.conn.execute(
            "SELECT COUNT(*) FROM tasks "
            "WHERE deadline = date('now') AND status='pending'"
        ).fetchone()[0]

        # Статистика выполнения по каждой категории
        cat_stats = self.conn.execute("""
            SELECT
                c.id,
                c.name,
                c.color,
                COUNT(t.id)                                   AS total,
                SUM(CASE WHEN t.status='done' THEN 1 ELSE 0 END) AS done
            FROM categories c
            LEFT JOIN tasks t ON t.category_id = c.id
            GROUP BY c.id
        """).fetchall()

        return {
            "total":     total,
            "done":      done,
            "overdue":   overdue,
            "today":     today_count,
            "cat_stats": cat_stats,
        }
