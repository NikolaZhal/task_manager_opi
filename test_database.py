"""
Юнит-тесты для модуля database.py.

Тестирует класс DatabaseManager: CRUD-операции над задачами
и категориями, а также сводную статистику.

Каждый тест работает с чистой in-memory базой данных (:memory:),
что гарантирует изолированность и независимость тестов.
"""

import sqlite3
import unittest
from datetime import date, timedelta

# Добавляем путь к исходникам проекта
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "task_manager"))

from database import DatabaseManager


class TestDatabaseInit(unittest.TestCase):
    """Тесты инициализации базы данных."""

    def setUp(self) -> None:
        """Создаёт чистую in-memory БД перед каждым тестом."""
        self.db = DatabaseManager(":memory:")

    def test_tables_created(self) -> None:
        """Таблицы tasks и categories создаются при инициализации."""
        tables = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {row["name"] for row in tables}
        self.assertIn("tasks", names)
        self.assertIn("categories", names)

    def test_default_categories_seeded(self) -> None:
        """При первом запуске создаются 3 стандартные категории."""
        cats = self.db.get_all_categories()
        self.assertEqual(len(cats), 3)

    def test_default_category_names(self) -> None:
        """Стандартные категории имеют правильные названия."""
        names = {c["name"] for c in self.db.get_all_categories()}
        self.assertEqual(names, {"Работа", "Личное", "Учёба"})

    def test_seed_idempotent(self) -> None:
        """Повторный вызов _seed_default_categories не дублирует записи."""
        self.db._seed_default_categories()
        cats = self.db.get_all_categories()
        self.assertEqual(len(cats), 3)


class TestTaskCRUD(unittest.TestCase):
    """Тесты CRUD-операций над задачами."""

    def setUp(self) -> None:
        """Создаёт БД и одну тестовую задачу."""
        self.db = DatabaseManager(":memory:")
        self.task_id = self.db.create_task(
            title="Тестовая задача",
            description="Описание",
            category_id=None,
            priority="medium",
            deadline=None,
            estimated_hours=2.0,
        )

    # ── create_task ───────────────────────────────────────────────────────────

    def test_create_task_returns_int(self) -> None:
        """create_task возвращает целочисленный id."""
        self.assertIsInstance(self.task_id, int)
        self.assertGreater(self.task_id, 0)

    def test_create_task_stored(self) -> None:
        """Созданная задача присутствует в get_all_tasks."""
        tasks = self.db.get_all_tasks()
        ids = [t["id"] for t in tasks]
        self.assertIn(self.task_id, ids)

    def test_create_task_fields(self) -> None:
        """Поля созданной задачи соответствуют переданным значениям."""
        task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
        self.assertEqual(task["title"], "Тестовая задача")
        self.assertEqual(task["description"], "Описание")
        self.assertEqual(task["priority"], "medium")
        self.assertEqual(task["status"], "pending")
        self.assertIsNone(task["deadline"])
        self.assertAlmostEqual(task["estimated_hours"], 2.0)

    def test_create_task_default_status_pending(self) -> None:
        """Новая задача всегда имеет статус 'pending'."""
        task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
        self.assertEqual(task["status"], "pending")

    def test_create_multiple_tasks(self) -> None:
        """Можно создать несколько задач с разными id."""
        id2 = self.db.create_task("Вторая", "", None, "low", None, 0)
        id3 = self.db.create_task("Третья", "", None, "high", None, 0)
        self.assertNotEqual(self.task_id, id2)
        self.assertNotEqual(id2, id3)
        self.assertEqual(len(self.db.get_all_tasks()), 3)

    # ── update_task ───────────────────────────────────────────────────────────

    def test_update_task_title(self) -> None:
        """update_task изменяет название задачи."""
        self.db.update_task(self.task_id, "Новое название", "", None, "low", None, 0)
        task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
        self.assertEqual(task["title"], "Новое название")

    def test_update_task_priority(self) -> None:
        """update_task изменяет приоритет задачи."""
        self.db.update_task(self.task_id, "Задача", "", None, "high", None, 0)
        task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
        self.assertEqual(task["priority"], "high")

    def test_update_task_deadline(self) -> None:
        """update_task сохраняет дедлайн в формате YYYY-MM-DD."""
        deadline = "2025-12-31"
        self.db.update_task(self.task_id, "Задача", "", None, "medium", deadline, 0)
        task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
        self.assertEqual(task["deadline"], deadline)

    def test_update_task_estimated_hours(self) -> None:
        """update_task сохраняет оценку времени."""
        self.db.update_task(self.task_id, "Задача", "", None, "medium", None, 4.5)
        task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
        self.assertAlmostEqual(task["estimated_hours"], 4.5)

    def test_update_nonexistent_task_no_error(self) -> None:
        """update_task на несуществующем id не вызывает исключения."""
        try:
            self.db.update_task(99999, "X", "", None, "low", None, 0)
        except Exception as e:
            self.fail(f"update_task вызвал исключение: {e}")

    # ── toggle_status ─────────────────────────────────────────────────────────

    def test_toggle_status_pending_to_done(self) -> None:
        """toggle_status переводит задачу из pending в done."""
        self.db.toggle_status(self.task_id)
        task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
        self.assertEqual(task["status"], "done")

    def test_toggle_status_done_to_pending(self) -> None:
        """Повторный toggle_status возвращает задачу из done в pending."""
        self.db.toggle_status(self.task_id)
        self.db.toggle_status(self.task_id)
        task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
        self.assertEqual(task["status"], "pending")

    def test_toggle_status_idempotent_sequence(self) -> None:
        """Три переключения: pending → done → pending → done."""
        for expected in ("done", "pending", "done"):
            self.db.toggle_status(self.task_id)
            task = next(t for t in self.db.get_all_tasks() if t["id"] == self.task_id)
            self.assertEqual(task["status"], expected)

    # ── delete_task ───────────────────────────────────────────────────────────

    def test_delete_task_removes_record(self) -> None:
        """delete_task удаляет задачу из таблицы."""
        self.db.delete_task(self.task_id)
        ids = [t["id"] for t in self.db.get_all_tasks()]
        self.assertNotIn(self.task_id, ids)

    def test_delete_task_count_decreases(self) -> None:
        """После удаления общее число задач уменьшается на 1."""
        before = len(self.db.get_all_tasks())
        self.db.delete_task(self.task_id)
        after = len(self.db.get_all_tasks())
        self.assertEqual(after, before - 1)

    def test_delete_nonexistent_task_no_error(self) -> None:
        """delete_task на несуществующем id не вызывает исключения."""
        try:
            self.db.delete_task(99999)
        except Exception as e:
            self.fail(f"delete_task вызвал исключение: {e}")

    # ── update_tracked_time ───────────────────────────────────────────────────

    def test_update_tracked_time_adds_seconds(self) -> None:
        """update_tracked_time прибавляет секунды к tracked_seconds."""
        self.db.update_tracked_time(self.task_id, 120)
        row = self.db.conn.execute(
            "SELECT tracked_seconds FROM tasks WHERE id=?", (self.task_id,)
        ).fetchone()
        self.assertEqual(row["tracked_seconds"], 120)

    def test_update_tracked_time_accumulates(self) -> None:
        """Повторный вызов накапливает секунды, а не перезаписывает."""
        self.db.update_tracked_time(self.task_id, 60)
        self.db.update_tracked_time(self.task_id, 40)
        row = self.db.conn.execute(
            "SELECT tracked_seconds FROM tasks WHERE id=?", (self.task_id,)
        ).fetchone()
        self.assertEqual(row["tracked_seconds"], 100)


class TestTaskQueries(unittest.TestCase):
    """Тесты выборочных запросов: today, overdue, category join."""

    def setUp(self) -> None:
        """Создаёт БД с набором задач с разными дедлайнами и статусами."""
        self.db = DatabaseManager(":memory:")
        today     = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tomorrow  = (date.today() + timedelta(days=1)).isoformat()

        # Задача на сегодня (pending)
        self.id_today = self.db.create_task(
            "Сегодня", "", None, "high", today, 0
        )
        # Просроченная задача (pending)
        self.id_overdue = self.db.create_task(
            "Просрочена", "", None, "medium", yesterday, 0
        )
        # Задача на завтра (pending)
        self.id_tomorrow = self.db.create_task(
            "Завтра", "", None, "low", tomorrow, 0
        )
        # Задача на сегодня, но выполнена — не должна попадать в today
        self.id_done_today = self.db.create_task(
            "Выполнена сегодня", "", None, "medium", today, 0
        )
        self.db.toggle_status(self.id_done_today)

    # ── get_tasks_today ───────────────────────────────────────────────────────

    def test_today_returns_only_today_pending(self) -> None:
        """get_tasks_today возвращает только незавершённые задачи с дедлайном сегодня."""
        tasks = self.db.get_tasks_today()
        ids = [t["id"] for t in tasks]
        self.assertIn(self.id_today, ids)
        self.assertNotIn(self.id_overdue, ids)
        self.assertNotIn(self.id_tomorrow, ids)
        self.assertNotIn(self.id_done_today, ids)

    def test_today_excludes_done(self) -> None:
        """get_tasks_today не возвращает выполненные задачи."""
        tasks = self.db.get_tasks_today()
        statuses = [t["status"] for t in tasks]
        self.assertTrue(all(s == "pending" for s in statuses))

    # ── get_overdue_tasks ─────────────────────────────────────────────────────

    def test_overdue_returns_past_deadline_pending(self) -> None:
        """get_overdue_tasks возвращает только незавершённые с истёкшим сроком."""
        tasks = self.db.get_overdue_tasks()
        ids = [t["id"] for t in tasks]
        self.assertIn(self.id_overdue, ids)
        self.assertNotIn(self.id_today, ids)
        self.assertNotIn(self.id_tomorrow, ids)

    def test_overdue_excludes_done(self) -> None:
        """get_overdue_tasks не возвращает выполненные просроченные задачи."""
        self.db.toggle_status(self.id_overdue)  # помечаем как выполненную
        tasks = self.db.get_overdue_tasks()
        ids = [t["id"] for t in tasks]
        self.assertNotIn(self.id_overdue, ids)

    # ── category join ─────────────────────────────────────────────────────────

    def test_get_all_tasks_includes_cat_name(self) -> None:
        """get_all_tasks возвращает cat_name из JOIN с categories."""
        cat_id = self.db.create_category("Тест", "#FF0000")
        task_id = self.db.create_task("С категорией", "", cat_id, "low", None, 0)
        task = next(t for t in self.db.get_all_tasks() if t["id"] == task_id)
        self.assertEqual(task["cat_name"], "Тест")

    def test_get_all_tasks_cat_name_none_without_category(self) -> None:
        """Задача без категории возвращает cat_name = None."""
        task = next(
            t for t in self.db.get_all_tasks() if t["id"] == self.id_today
        )
        self.assertIsNone(task["cat_name"])


class TestCategoryCRUD(unittest.TestCase):
    """Тесты CRUD-операций над категориями."""

    def setUp(self) -> None:
        """Создаёт чистую БД."""
        self.db = DatabaseManager(":memory:")

    # ── create_category ───────────────────────────────────────────────────────

    def test_create_category_returns_int(self) -> None:
        """create_category возвращает целочисленный id."""
        cat_id = self.db.create_category("Новая", "#AABBCC")
        self.assertIsInstance(cat_id, int)
        self.assertGreater(cat_id, 0)

    def test_create_category_stored(self) -> None:
        """Созданная категория присутствует в get_all_categories."""
        self.db.create_category("Спорт", "#FF5500")
        names = [c["name"] for c in self.db.get_all_categories()]
        self.assertIn("Спорт", names)

    def test_create_category_color_stored(self) -> None:
        """Цвет категории сохраняется корректно."""
        self.db.create_category("Цветная", "#123456")
        cat = next(c for c in self.db.get_all_categories() if c["name"] == "Цветная")
        self.assertEqual(cat["color"], "#123456")

    def test_create_duplicate_category_raises(self) -> None:
        """Создание категории с дублирующимся именем вызывает IntegrityError."""
        self.db.create_category("Уникальная", "#000000")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.create_category("Уникальная", "#FFFFFF")

    # ── update_category ───────────────────────────────────────────────────────

    def test_update_category_name(self) -> None:
        """update_category изменяет название категории."""
        cat_id = self.db.create_category("Старое", "#000000")
        self.db.update_category(cat_id, "Новое", "#000000")
        cat = next(c for c in self.db.get_all_categories() if c["id"] == cat_id)
        self.assertEqual(cat["name"], "Новое")

    def test_update_category_color(self) -> None:
        """update_category изменяет цвет категории."""
        cat_id = self.db.create_category("Категория", "#000000")
        self.db.update_category(cat_id, "Категория", "#ABCDEF")
        cat = next(c for c in self.db.get_all_categories() if c["id"] == cat_id)
        self.assertEqual(cat["color"], "#ABCDEF")

    # ── delete_category ───────────────────────────────────────────────────────

    def test_delete_category_removes_record(self) -> None:
        """delete_category удаляет запись из таблицы."""
        cat_id = self.db.create_category("Удаляемая", "#000000")
        self.db.delete_category(cat_id)
        names = [c["name"] for c in self.db.get_all_categories()]
        self.assertNotIn("Удаляемая", names)

    def test_delete_category_nullifies_task_category(self) -> None:
        """После удаления категории связанные задачи получают category_id = NULL."""
        cat_id = self.db.create_category("Временная", "#000000")
        task_id = self.db.create_task("Задача", "", cat_id, "low", None, 0)
        self.db.delete_category(cat_id)
        task = next(t for t in self.db.get_all_tasks() if t["id"] == task_id)
        self.assertIsNone(task["category_id"])

    def test_get_all_categories_sorted_by_name(self) -> None:
        """get_all_categories возвращает записи в алфавитном порядке."""
        self.db.create_category("Я", "#000000")
        self.db.create_category("А", "#000000")
        names = [c["name"] for c in self.db.get_all_categories()]
        self.assertEqual(names, sorted(names))


class TestStats(unittest.TestCase):
    """Тесты метода get_stats."""

    def setUp(self) -> None:
        """Создаёт БД с известным набором задач."""
        self.db = DatabaseManager(":memory:")
        today     = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        self.id1 = self.db.create_task("Задача 1", "", None, "high", today, 0)
        self.id2 = self.db.create_task("Задача 2", "", None, "low", yesterday, 0)
        self.id3 = self.db.create_task("Задача 3", "", None, "medium", None, 0)
        # Делаем id1 и id3 выполненными
        self.db.toggle_status(self.id1)
        self.db.toggle_status(self.id3)

    def test_stats_total(self) -> None:
        """get_stats возвращает корректное общее число задач."""
        self.assertEqual(self.db.get_stats()["total"], 3)

    def test_stats_done(self) -> None:
        """get_stats возвращает корректное число выполненных задач."""
        self.assertEqual(self.db.get_stats()["done"], 2)

    def test_stats_overdue(self) -> None:
        """get_stats возвращает корректное число просроченных задач."""
        # id2: вчера + pending — просрочена
        self.assertEqual(self.db.get_stats()["overdue"], 1)

    def test_stats_today(self) -> None:
        """get_stats возвращает корректное число задач на сегодня (pending)."""
        # id1 был на сегодня, но мы его выполнили — today = 0
        self.assertEqual(self.db.get_stats()["today"], 0)

    def test_stats_today_counts_pending_only(self) -> None:
        """Задача на сегодня со статусом pending учитывается в today."""
        new_id = self.db.create_task(
            "Сегодня pending", "", None, "low", date.today().isoformat(), 0
        )
        self.assertEqual(self.db.get_stats()["today"], 1)

    def test_stats_cat_stats_contains_all_categories(self) -> None:
        """cat_stats содержит строку для каждой существующей категории."""
        cat_count = len(self.db.get_all_categories())
        self.assertEqual(len(self.db.get_stats()["cat_stats"]), cat_count)

    def test_stats_empty_db(self) -> None:
        """get_stats на пустой (без задач) БД возвращает нули."""
        fresh = DatabaseManager(":memory:")
        stats = fresh.get_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["done"], 0)
        self.assertEqual(stats["overdue"], 0)
        self.assertEqual(stats["today"], 0)

    def test_stats_after_delete(self) -> None:
        """get_stats обновляется после удаления задачи."""
        self.db.delete_task(self.id3)
        stats = self.db.get_stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["done"], 1)  # только id1 осталась выполненной


if __name__ == "__main__":
    unittest.main(verbosity=2)
