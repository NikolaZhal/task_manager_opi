import sqlite3
from datetime import date


class DatabaseManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_default_categories()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL DEFAULT '#4A90D9'
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category_id INTEGER,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                deadline TEXT,
                estimated_hours REAL DEFAULT 0,
                tracked_seconds INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (date('now')),
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );
        """)
        self.conn.commit()

    def _seed_default_categories(self):
        defaults = [("Работа", "#4A90D9"), ("Личное", "#2ECC71"), ("Учёба", "#F39C12")]
        for name, color in defaults:
            try:
                self.conn.execute(
                    "INSERT INTO categories (name, color) VALUES (?, ?)", (name, color)
                )
            except sqlite3.IntegrityError:
                pass
        self.conn.commit()

    # ── TASKS ──────────────────────────────────────────────
    def get_all_tasks(self):
        return self.conn.execute(
            "SELECT t.*, c.name as cat_name, c.color as cat_color "
            "FROM tasks t LEFT JOIN categories c ON t.category_id = c.id "
            "ORDER BY t.created_at DESC"
        ).fetchall()

    def get_tasks_today(self):
        today = date.today().isoformat()
        return self.conn.execute(
            "SELECT t.*, c.name as cat_name, c.color as cat_color "
            "FROM tasks t LEFT JOIN categories c ON t.category_id = c.id "
            "WHERE t.deadline = ? AND t.status = 'pending' ORDER BY t.priority",
            (today,)
        ).fetchall()

    def get_overdue_tasks(self):
        today = date.today().isoformat()
        return self.conn.execute(
            "SELECT t.*, c.name as cat_name, c.color as cat_color "
            "FROM tasks t LEFT JOIN categories c ON t.category_id = c.id "
            "WHERE t.deadline < ? AND t.status = 'pending' ORDER BY t.deadline",
            (today,)
        ).fetchall()

    def create_task(self, title, description, category_id, priority, deadline,
                    estimated_hours):
        cur = self.conn.execute(
            "INSERT INTO tasks (title, description, category_id, priority, deadline, "
            "estimated_hours) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, category_id, priority, deadline or None, estimated_hours)
        )
        self.conn.commit()
        return cur.lastrowid

    def update_task(self, task_id, title, description, category_id, priority,
                    deadline, estimated_hours):
        self.conn.execute(
            "UPDATE tasks SET title=?, description=?, category_id=?, priority=?, "
            "deadline=?, estimated_hours=? WHERE id=?",
            (title, description, category_id, priority, deadline or None,
             estimated_hours, task_id)
        )
        self.conn.commit()

    def toggle_status(self, task_id):
        row = self.conn.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
        new_status = "done" if row["status"] == "pending" else "pending"
        self.conn.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def update_tracked_time(self, task_id, seconds):
        self.conn.execute(
            "UPDATE tasks SET tracked_seconds = tracked_seconds + ? WHERE id=?",
            (seconds, task_id)
        )
        self.conn.commit()

    # ── CATEGORIES ─────────────────────────────────────────
    def get_all_categories(self):
        return self.conn.execute("SELECT * FROM categories ORDER BY name").fetchall()

    def create_category(self, name, color):
        cur = self.conn.execute(
            "INSERT INTO categories (name, color) VALUES (?, ?)", (name, color)
        )
        self.conn.commit()
        return cur.lastrowid

    def update_category(self, cat_id, name, color):
        self.conn.execute(
            "UPDATE categories SET name=?, color=? WHERE id=?", (name, color, cat_id)
        )
        self.conn.commit()

    def delete_category(self, cat_id):
        self.conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
        self.conn.commit()

    # ── STATS ──────────────────────────────────────────────
    def get_stats(self):
        total = self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done = self.conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status='done'"
        ).fetchone()[0]
        overdue = self.conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE deadline < date('now') AND status='pending'"
        ).fetchone()[0]
        today_count = self.conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE deadline = date('now') AND status='pending'"
        ).fetchone()[0]

        cat_stats = self.conn.execute("""
            SELECT c.id, c.name, c.color,
                   COUNT(t.id) as total,
                   SUM(CASE WHEN t.status='done' THEN 1 ELSE 0 END) as done
            FROM categories c
            LEFT JOIN tasks t ON t.category_id = c.id
            GROUP BY c.id
        """).fetchall()

        return {
            "total": total, "done": done,
            "overdue": overdue, "today": today_count,
            "cat_stats": cat_stats
        }
