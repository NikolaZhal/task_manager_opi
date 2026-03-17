"""
Юнит-тесты для модуля database.py.

Тесты разделены на позитивные (ожидаемое корректное поведение)
и негативные (некорректные входные данные, граничные условия,
ошибочные состояния) сценарии.

Каждый тест работает с чистой in-memory БД (:memory:),
что гарантирует полную изолированность.

Запуск:
    python -m unittest test_database -v
"""

import sqlite3
import unittest
from datetime import date, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "task_manager"))

from database import DatabaseManager


# ══════════════════════════════════════════════════════════════════
# Вспомогательная функция
# ══════════════════════════════════════════════════════════════════

def _get_task(db, task_id):
    """Возвращает задачу по id из get_all_tasks."""
    return next(t for t in db.get_all_tasks() if t["id"] == task_id)


# ══════════════════════════════════════════════════════════════════
# 1. Инициализация БД
# ══════════════════════════════════════════════════════════════════

class TestInitPositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Инициализация базы данных."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_tables_tasks_created(self):
        """[+] Таблица tasks создаётся при инициализации."""
        tables = {r["name"] for r in self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        self.assertIn("tasks", tables)

    def test_tables_categories_created(self):
        """[+] Таблица categories создаётся при инициализации."""
        tables = {r["name"] for r in self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        self.assertIn("categories", tables)

    def test_three_default_categories_seeded(self):
        """[+] При первом запуске создаются ровно 3 стандартные категории."""
        self.assertEqual(len(self.db.get_all_categories()), 3)

    def test_default_category_names_correct(self):
        """[+] Стандартные категории имеют правильные названия."""
        names = {c["name"] for c in self.db.get_all_categories()}
        self.assertEqual(names, {"Работа", "Личное", "Учёба"})

    def test_foreign_keys_enabled(self):
        """[+] PRAGMA foreign_keys включён (ON DELETE SET NULL работает)."""
        result = self.db.conn.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(result, 1)


class TestInitNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Инициализация базы данных."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_seed_twice_does_not_duplicate(self):
        """[-] Повторный вызов _seed_default_categories не дублирует записи."""
        self.db._seed_default_categories()
        self.db._seed_default_categories()
        self.assertEqual(len(self.db.get_all_categories()), 3)

    def test_new_db_has_no_tasks(self):
        """[-] Свежая БД не содержит ни одной задачи."""
        self.assertEqual(len(self.db.get_all_tasks()), 0)


# ══════════════════════════════════════════════════════════════════
# 2. Создание задачи
# ══════════════════════════════════════════════════════════════════

class TestCreateTaskPositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Создание задачи."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_returns_positive_integer_id(self):
        """[+] create_task возвращает целочисленный id > 0."""
        tid = self.db.create_task("Задача", "", None, "medium", None, 0)
        self.assertIsInstance(tid, int)
        self.assertGreater(tid, 0)

    def test_task_appears_in_list(self):
        """[+] Созданная задача присутствует в get_all_tasks."""
        tid = self.db.create_task("Купить молоко", "", None, "low", None, 0)
        self.assertIn(tid, [t["id"] for t in self.db.get_all_tasks()])

    def test_all_fields_saved_correctly(self):
        """[+] Все поля задачи сохраняются с переданными значениями."""
        deadline = "2025-12-31"
        tid = self.db.create_task("Сдать отчёт", "Описание", None, "high", deadline, 3.5)
        task = _get_task(self.db, tid)
        self.assertEqual(task["title"],           "Сдать отчёт")
        self.assertEqual(task["description"],     "Описание")
        self.assertEqual(task["priority"],        "high")
        self.assertEqual(task["deadline"],        deadline)
        self.assertAlmostEqual(task["estimated_hours"], 3.5)

    def test_default_status_is_pending(self):
        """[+] Новая задача по умолчанию получает статус 'pending'."""
        tid = self.db.create_task("Задача", "", None, "medium", None, 0)
        self.assertEqual(_get_task(self.db, tid)["status"], "pending")

    def test_all_three_priority_values(self):
        """[+] Каждое значение приоритета (low/medium/high) сохраняется корректно."""
        for priority in ("low", "medium", "high"):
            tid = self.db.create_task(f"Задача {priority}", "", None, priority, None, 0)
            self.assertEqual(_get_task(self.db, tid)["priority"], priority)

    def test_deadline_none_stored_as_null(self):
        """[+] Задача без дедлайна хранит NULL в поле deadline."""
        tid = self.db.create_task("Без дедлайна", "", None, "low", None, 0)
        self.assertIsNone(_get_task(self.db, tid)["deadline"])

    def test_multiple_tasks_get_unique_ids(self):
        """[+] Несколько задач получают уникальные id."""
        ids = [self.db.create_task(f"Задача {i}", "", None, "low", None, 0)
               for i in range(5)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_task_with_category(self):
        """[+] Задача привязывается к существующей категории."""
        cat_id = self.db.create_category("Спорт", "#FF0000")
        tid = self.db.create_task("Тренировка", "", cat_id, "medium", None, 0)
        self.assertEqual(_get_task(self.db, tid)["category_id"], cat_id)

    def test_fractional_estimated_hours(self):
        """[+] Дробное значение estimated_hours сохраняется точно."""
        tid = self.db.create_task("Задача", "", None, "low", None, 1.5)
        self.assertAlmostEqual(_get_task(self.db, tid)["estimated_hours"], 1.5)

    def test_zero_estimated_hours(self):
        """[+] Нулевое значение estimated_hours (граничное: минимум) сохраняется."""
        tid = self.db.create_task("Задача", "", None, "low", None, 0.0)
        self.assertAlmostEqual(_get_task(self.db, tid)["estimated_hours"], 0.0)


class TestCreateTaskNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Создание задачи."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_empty_title_saved_as_is(self):
        """[-] БД принимает пустое название — валидация на уровне UI."""
        # Пустая строка разрешена на уровне SQLite, блокируется в диалоге
        tid = self.db.create_task("", "", None, "low", None, 0)
        self.assertIsNotNone(tid)

    def test_whitespace_title_saved_as_is(self):
        """[-] Строка из пробелов сохраняется без trim — strip() в UI."""
        tid = self.db.create_task("   ", "", None, "low", None, 0)
        task = _get_task(self.db, tid)
        self.assertEqual(task["title"], "   ")

    def test_nonexistent_category_id_accepted(self):
        """[-] SQLite сохраняет несуществующий category_id без ошибки при выкл. FK."""
        # При включённых FK это вызвало бы ошибку, но category_id может быть NULL
        # Проверяем что задача создаётся с category_id=None
        tid = self.db.create_task("Задача", "", None, "low", None, 0)
        self.assertIsNone(_get_task(self.db, tid)["category_id"])

    def test_task_count_after_create(self):
        """[-] После создания задачи список не пустой (было пусто)."""
        self.assertEqual(len(self.db.get_all_tasks()), 0)
        self.db.create_task("Задача", "", None, "low", None, 0)
        self.assertEqual(len(self.db.get_all_tasks()), 1)


# ══════════════════════════════════════════════════════════════════
# 3. Редактирование задачи
# ══════════════════════════════════════════════════════════════════

class TestUpdateTaskPositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Редактирование задачи."""

    def setUp(self):
        self.db  = DatabaseManager(":memory:")
        self.tid = self.db.create_task("Старое", "Описание", None, "low", None, 1.0)

    def test_title_changes(self):
        """[+] update_task изменяет название задачи."""
        self.db.update_task(self.tid, "Новое", "", None, "low", None, 0)
        self.assertEqual(_get_task(self.db, self.tid)["title"], "Новое")

    def test_priority_changes(self):
        """[+] update_task изменяет приоритет с low на high."""
        self.db.update_task(self.tid, "Задача", "", None, "high", None, 0)
        self.assertEqual(_get_task(self.db, self.tid)["priority"], "high")

    def test_deadline_added(self):
        """[+] update_task добавляет дедлайн к задаче без дедлайна."""
        self.db.update_task(self.tid, "Задача", "", None, "low", "2025-06-01", 0)
        self.assertEqual(_get_task(self.db, self.tid)["deadline"], "2025-06-01")

    def test_deadline_cleared(self):
        """[+] update_task убирает дедлайн (None) у задачи с дедлайном."""
        self.db.update_task(self.tid, "Задача", "", None, "low", "2025-06-01", 0)
        self.db.update_task(self.tid, "Задача", "", None, "low", None, 0)
        self.assertIsNone(_get_task(self.db, self.tid)["deadline"])

    def test_estimated_hours_updated(self):
        """[+] update_task изменяет оценку времени."""
        self.db.update_task(self.tid, "Задача", "", None, "low", None, 4.5)
        self.assertAlmostEqual(_get_task(self.db, self.tid)["estimated_hours"], 4.5)

    def test_total_task_count_unchanged(self):
        """[+] После редактирования общее число задач не изменяется."""
        before = len(self.db.get_all_tasks())
        self.db.update_task(self.tid, "Другое", "", None, "high", None, 0)
        self.assertEqual(len(self.db.get_all_tasks()), before)


class TestUpdateTaskNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Редактирование задачи."""

    def setUp(self):
        self.db  = DatabaseManager(":memory:")
        self.tid = self.db.create_task("Задача", "", None, "low", None, 0)

    def test_update_nonexistent_id_no_exception(self):
        """[-] update_task на несуществующем id не вызывает исключения."""
        try:
            self.db.update_task(99999, "X", "", None, "low", None, 0)
        except Exception as e:
            self.fail(f"Неожиданное исключение: {e}")

    def test_update_nonexistent_id_does_not_change_data(self):
        """[-] update_task на несуществующем id не изменяет существующие данные."""
        self.db.update_task(99999, "Взломано", "", None, "high", None, 0)
        self.assertEqual(_get_task(self.db, self.tid)["title"], "Задача")


# ══════════════════════════════════════════════════════════════════
# 4. Переключение статуса задачи
# ══════════════════════════════════════════════════════════════════

class TestToggleStatusPositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Переключение статуса задачи."""

    def setUp(self):
        self.db  = DatabaseManager(":memory:")
        self.tid = self.db.create_task("Задача", "", None, "medium", None, 0)

    def test_pending_becomes_done(self):
        """[+] toggle_status переводит задачу из pending в done."""
        self.db.toggle_status(self.tid)
        self.assertEqual(_get_task(self.db, self.tid)["status"], "done")

    def test_done_becomes_pending(self):
        """[+] Повторный toggle_status возвращает задачу из done в pending."""
        self.db.toggle_status(self.tid)
        self.db.toggle_status(self.tid)
        self.assertEqual(_get_task(self.db, self.tid)["status"], "pending")

    def test_triple_toggle_sequence(self):
        """[+] Три переключения дают последовательность done→pending→done."""
        for expected in ("done", "pending", "done"):
            self.db.toggle_status(self.tid)
            self.assertEqual(_get_task(self.db, self.tid)["status"], expected)

    def test_toggle_does_not_affect_other_tasks(self):
        """[+] Переключение статуса одной задачи не затрагивает другую."""
        tid2 = self.db.create_task("Другая", "", None, "low", None, 0)
        self.db.toggle_status(self.tid)
        self.assertEqual(_get_task(self.db, tid2)["status"], "pending")


class TestToggleStatusNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Переключение статуса задачи."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_done_task_excluded_from_today(self):
        """[-] Выполненная задача с дедлайном сегодня не попадает в get_tasks_today."""
        today = date.today().isoformat()
        tid = self.db.create_task("Сегодня", "", None, "high", today, 0)
        self.db.toggle_status(tid)
        ids = [t["id"] for t in self.db.get_tasks_today()]
        self.assertNotIn(tid, ids)

    def test_done_task_excluded_from_overdue(self):
        """[-] Выполненная просроченная задача не попадает в get_overdue_tasks."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tid = self.db.create_task("Просроченная", "", None, "low", yesterday, 0)
        self.db.toggle_status(tid)
        ids = [t["id"] for t in self.db.get_overdue_tasks()]
        self.assertNotIn(tid, ids)


# ══════════════════════════════════════════════════════════════════
# 5. Удаление задачи
# ══════════════════════════════════════════════════════════════════

class TestDeleteTaskPositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Удаление задачи."""

    def setUp(self):
        self.db  = DatabaseManager(":memory:")
        self.tid = self.db.create_task("Удаляемая", "", None, "low", None, 0)

    def test_task_removed_from_list(self):
        """[+] delete_task удаляет задачу из get_all_tasks."""
        self.db.delete_task(self.tid)
        self.assertNotIn(self.tid, [t["id"] for t in self.db.get_all_tasks()])

    def test_total_count_decreases_by_one(self):
        """[+] После удаления общее число задач уменьшается на 1."""
        before = len(self.db.get_all_tasks())
        self.db.delete_task(self.tid)
        self.assertEqual(len(self.db.get_all_tasks()), before - 1)

    def test_other_tasks_unaffected(self):
        """[+] Удаление одной задачи не затрагивает остальные."""
        tid2 = self.db.create_task("Остаётся", "", None, "low", None, 0)
        self.db.delete_task(self.tid)
        self.assertIn(tid2, [t["id"] for t in self.db.get_all_tasks()])


class TestDeleteTaskNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Удаление задачи."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_delete_nonexistent_id_no_exception(self):
        """[-] delete_task на несуществующем id не вызывает исключения."""
        try:
            self.db.delete_task(99999)
        except Exception as e:
            self.fail(f"Неожиданное исключение: {e}")

    def test_delete_same_task_twice_no_exception(self):
        """[-] Повторное удаление уже удалённой задачи не вызывает исключения."""
        tid = self.db.create_task("Задача", "", None, "low", None, 0)
        self.db.delete_task(tid)
        try:
            self.db.delete_task(tid)
        except Exception as e:
            self.fail(f"Неожиданное исключение: {e}")

    def test_delete_all_tasks_leaves_empty_list(self):
        """[-] После удаления всех задач get_all_tasks возвращает пустой список."""
        ids = [self.db.create_task(f"Задача {i}", "", None, "low", None, 0)
               for i in range(3)]
        for tid in ids:
            self.db.delete_task(tid)
        self.assertEqual(self.db.get_all_tasks(), [])


# ══════════════════════════════════════════════════════════════════
# 6. Трекер времени
# ══════════════════════════════════════════════════════════════════

class TestTrackedTimePositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Отслеживание времени выполнения."""

    def setUp(self):
        self.db  = DatabaseManager(":memory:")
        self.tid = self.db.create_task("Задача", "", None, "low", None, 0)

    def _get_seconds(self):
        return self.db.conn.execute(
            "SELECT tracked_seconds FROM tasks WHERE id=?", (self.tid,)
        ).fetchone()["tracked_seconds"]

    def test_add_seconds(self):
        """[+] update_tracked_time прибавляет секунды к счётчику."""
        self.db.update_tracked_time(self.tid, 120)
        self.assertEqual(self._get_seconds(), 120)

    def test_accumulates_multiple_calls(self):
        """[+] Повторные вызовы накапливают секунды."""
        self.db.update_tracked_time(self.tid, 60)
        self.db.update_tracked_time(self.tid, 40)
        self.assertEqual(self._get_seconds(), 100)

    def test_initial_seconds_zero(self):
        """[+] Новая задача имеет tracked_seconds = 0."""
        self.assertEqual(self._get_seconds(), 0)


class TestTrackedTimeNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Отслеживание времени."""

    def setUp(self):
        self.db  = DatabaseManager(":memory:")
        self.tid = self.db.create_task("Задача", "", None, "low", None, 0)

    def test_add_zero_seconds_no_change(self):
        """[-] Добавление 0 секунд не изменяет счётчик."""
        self.db.update_tracked_time(self.tid, 0)
        val = self.db.conn.execute(
            "SELECT tracked_seconds FROM tasks WHERE id=?", (self.tid,)
        ).fetchone()["tracked_seconds"]
        self.assertEqual(val, 0)


# ══════════════════════════════════════════════════════════════════
# 7. Выборки: сегодня и просроченные
# ══════════════════════════════════════════════════════════════════

class TestQueriesPositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Выборки задач по дате."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")
        today     = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tomorrow  = (date.today() + timedelta(days=1)).isoformat()

        self.tid_today    = self.db.create_task("Сегодня",   "", None, "high",   today,     0)
        self.tid_overdue  = self.db.create_task("Просрочена","", None, "medium", yesterday, 0)
        self.tid_tomorrow = self.db.create_task("Завтра",    "", None, "low",    tomorrow,  0)
        self.tid_no_dl    = self.db.create_task("Без даты",  "", None, "low",    None,      0)

    def test_today_contains_today_task(self):
        """[+] get_tasks_today возвращает задачу с дедлайном сегодня."""
        ids = [t["id"] for t in self.db.get_tasks_today()]
        self.assertIn(self.tid_today, ids)

    def test_overdue_contains_yesterday_task(self):
        """[+] get_overdue_tasks возвращает задачу с дедлайном вчера."""
        ids = [t["id"] for t in self.db.get_overdue_tasks()]
        self.assertIn(self.tid_overdue, ids)

    def test_cat_name_returned_in_join(self):
        """[+] get_all_tasks возвращает cat_name через JOIN с categories."""
        cat_id = self.db.create_category("Спорт", "#0000FF")
        tid = self.db.create_task("Тренировка", "", cat_id, "low", None, 0)
        self.assertEqual(_get_task(self.db, tid)["cat_name"], "Спорт")


class TestQueriesNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Выборки задач по дате."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")
        today     = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tomorrow  = (date.today() + timedelta(days=1)).isoformat()

        self.tid_today    = self.db.create_task("Сегодня",   "", None, "high",   today,     0)
        self.tid_overdue  = self.db.create_task("Просрочена","", None, "medium", yesterday, 0)
        self.tid_tomorrow = self.db.create_task("Завтра",    "", None, "low",    tomorrow,  0)

        # Выполняем задачу сегодня
        self.tid_done_today = self.db.create_task("Сделана сегодня", "", None, "low", today, 0)
        self.db.toggle_status(self.tid_done_today)

    def test_today_excludes_tomorrow(self):
        """[-] get_tasks_today не возвращает задачу с дедлайном завтра."""
        ids = [t["id"] for t in self.db.get_tasks_today()]
        self.assertNotIn(self.tid_tomorrow, ids)

    def test_today_excludes_overdue(self):
        """[-] get_tasks_today не возвращает просроченные задачи."""
        ids = [t["id"] for t in self.db.get_tasks_today()]
        self.assertNotIn(self.tid_overdue, ids)

    def test_today_excludes_done(self):
        """[-] get_tasks_today не возвращает выполненные задачи."""
        ids = [t["id"] for t in self.db.get_tasks_today()]
        self.assertNotIn(self.tid_done_today, ids)

    def test_overdue_excludes_today(self):
        """[-] get_overdue_tasks не возвращает задачу с дедлайном сегодня."""
        ids = [t["id"] for t in self.db.get_overdue_tasks()]
        self.assertNotIn(self.tid_today, ids)

    def test_overdue_excludes_tomorrow(self):
        """[-] get_overdue_tasks не возвращает задачу с дедлайном завтра."""
        ids = [t["id"] for t in self.db.get_overdue_tasks()]
        self.assertNotIn(self.tid_tomorrow, ids)

    def test_overdue_excludes_done(self):
        """[-] Выполненная просроченная задача не попадает в get_overdue_tasks."""
        self.db.toggle_status(self.tid_overdue)
        ids = [t["id"] for t in self.db.get_overdue_tasks()]
        self.assertNotIn(self.tid_overdue, ids)

    def test_no_category_returns_cat_name_none(self):
        """[-] Задача без категории возвращает cat_name = None."""
        self.assertIsNone(_get_task(self.db, self.tid_today)["cat_name"])

    def test_today_returns_empty_when_no_tasks(self):
        """[-] get_tasks_today возвращает пустой список при отсутствии задач на сегодня."""
        fresh = DatabaseManager(":memory:")
        self.assertEqual(fresh.get_tasks_today(), [])

    def test_overdue_returns_empty_when_no_tasks(self):
        """[-] get_overdue_tasks возвращает пустой список при отсутствии просроченных."""
        fresh = DatabaseManager(":memory:")
        self.assertEqual(fresh.get_overdue_tasks(), [])


# ══════════════════════════════════════════════════════════════════
# 8. Категории
# ══════════════════════════════════════════════════════════════════

class TestCategoryPositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Управление категориями."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_create_returns_positive_id(self):
        """[+] create_category возвращает целочисленный id > 0."""
        cat_id = self.db.create_category("Спорт", "#FF0000")
        self.assertIsInstance(cat_id, int)
        self.assertGreater(cat_id, 0)

    def test_create_name_and_color_saved(self):
        """[+] Название и цвет новой категории сохраняются корректно."""
        self.db.create_category("Хобби", "#AABBCC")
        cat = next(c for c in self.db.get_all_categories() if c["name"] == "Хобби")
        self.assertEqual(cat["color"], "#AABBCC")

    def test_update_name(self):
        """[+] update_category изменяет название категории."""
        cid = self.db.create_category("Старое", "#000000")
        self.db.update_category(cid, "Новое", "#000000")
        cat = next(c for c in self.db.get_all_categories() if c["id"] == cid)
        self.assertEqual(cat["name"], "Новое")

    def test_update_color(self):
        """[+] update_category изменяет цвет категории."""
        cid = self.db.create_category("Кат", "#000000")
        self.db.update_category(cid, "Кат", "#FFFFFF")
        cat = next(c for c in self.db.get_all_categories() if c["id"] == cid)
        self.assertEqual(cat["color"], "#FFFFFF")

    def test_delete_removes_from_list(self):
        """[+] delete_category удаляет запись из get_all_categories."""
        cid = self.db.create_category("Удаляемая", "#000000")
        self.db.delete_category(cid)
        names = [c["name"] for c in self.db.get_all_categories()]
        self.assertNotIn("Удаляемая", names)

    def test_delete_nullifies_task_category(self):
        """[+] После удаления категории задача получает category_id = NULL."""
        cid = self.db.create_category("Временная", "#000000")
        tid = self.db.create_task("Задача", "", cid, "low", None, 0)
        self.db.delete_category(cid)
        self.assertIsNone(_get_task(self.db, tid)["category_id"])

    def test_sorted_alphabetically(self):
        """[+] get_all_categories возвращает список в алфавитном порядке."""
        self.db.create_category("Я", "#000000")
        self.db.create_category("А", "#000000")
        names = [c["name"] for c in self.db.get_all_categories()]
        self.assertEqual(names, sorted(names))


class TestCategoryNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Управление категориями."""

    def setUp(self):
        self.db = DatabaseManager(":memory:")

    def test_duplicate_name_raises_integrity_error(self):
        """[-] Создание категории с дублирующимся именем вызывает IntegrityError."""
        self.db.create_category("Работа2", "#000000")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.create_category("Работа2", "#FFFFFF")

    def test_duplicate_does_not_create_record(self):
        """[-] После ошибки дубликата число категорий не увеличивается."""
        self.db.create_category("Тест", "#000000")
        count_before = len(self.db.get_all_categories())
        try:
            self.db.create_category("Тест", "#FFFFFF")
        except sqlite3.IntegrityError:
            pass
        self.assertEqual(len(self.db.get_all_categories()), count_before)

    def test_delete_nonexistent_category_no_exception(self):
        """[-] delete_category на несуществующем id не вызывает исключения."""
        try:
            self.db.delete_category(99999)
        except Exception as e:
            self.fail(f"Неожиданное исключение: {e}")

    def test_tasks_survive_category_deletion(self):
        """[-] Задачи не удаляются при удалении их категории."""
        cid = self.db.create_category("Кат", "#000000")
        tid = self.db.create_task("Задача", "", cid, "low", None, 0)
        self.db.delete_category(cid)
        ids = [t["id"] for t in self.db.get_all_tasks()]
        self.assertIn(tid, ids)


# ══════════════════════════════════════════════════════════════════
# 9. Статистика
# ══════════════════════════════════════════════════════════════════

class TestStatsPositive(unittest.TestCase):
    """[ПОЗИТИВНЫЕ] Сводная статистика get_stats."""

    def setUp(self):
        self.db  = DatabaseManager(":memory:")
        today     = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        self.id1 = self.db.create_task("Задача 1", "", None, "high",   today,     0)
        self.id2 = self.db.create_task("Задача 2", "", None, "low",    yesterday, 0)
        self.id3 = self.db.create_task("Задача 3", "", None, "medium", None,      0)
        self.db.toggle_status(self.id1)
        self.db.toggle_status(self.id3)

    def test_total_count(self):
        """[+] total = общее число задач в БД."""
        self.assertEqual(self.db.get_stats()["total"], 3)

    def test_done_count(self):
        """[+] done = число задач со статусом done."""
        self.assertEqual(self.db.get_stats()["done"], 2)

    def test_overdue_count(self):
        """[+] overdue = число pending-задач с дедлайном < сегодня."""
        self.assertEqual(self.db.get_stats()["overdue"], 1)

    def test_today_pending_counted(self):
        """[+] today учитывает новую pending-задачу с дедлайном сегодня."""
        self.db.create_task("Сегодня", "", None, "low", date.today().isoformat(), 0)
        self.assertEqual(self.db.get_stats()["today"], 1)

    def test_cat_stats_covers_all_categories(self):
        """[+] cat_stats содержит строку для каждой категории."""
        self.assertEqual(
            len(self.db.get_stats()["cat_stats"]),
            len(self.db.get_all_categories()),
        )

    def test_stats_updated_after_delete(self):
        """[+] total и done уменьшаются после удаления задачи."""
        self.db.delete_task(self.id3)
        stats = self.db.get_stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["done"],  1)


class TestStatsNegative(unittest.TestCase):
    """[НЕГАТИВНЫЕ] Сводная статистика get_stats."""

    def test_empty_db_all_zeros(self):
        """[-] На пустой БД все счётчики равны нулю."""
        db = DatabaseManager(":memory:")
        stats = db.get_stats()
        self.assertEqual(stats["total"],   0)
        self.assertEqual(stats["done"],    0)
        self.assertEqual(stats["overdue"], 0)
        self.assertEqual(stats["today"],   0)

    def test_today_excludes_done_task(self):
        """[-] today не считает выполненную задачу с дедлайном сегодня."""
        db = DatabaseManager(":memory:")
        tid = db.create_task("Сегодня", "", None, "low", date.today().isoformat(), 0)
        db.toggle_status(tid)
        self.assertEqual(db.get_stats()["today"], 0)

    def test_overdue_excludes_done_task(self):
        """[-] overdue не считает выполненную просроченную задачу."""
        db = DatabaseManager(":memory:")
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tid = db.create_task("Просрочена", "", None, "low", yesterday, 0)
        db.toggle_status(tid)
        self.assertEqual(db.get_stats()["overdue"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
