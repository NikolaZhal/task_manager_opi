"""
Точка входа приложения «Система управления задачами».

Запускает Qt-приложение, инициализирует базу данных
и открывает главное окно.

Использование:
    python main.py
"""

import os
import sys

# Исправляем путь к Qt-плагинам платформы (необходимо до первого импорта PyQt5)
try:
    import PyQt5
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(
        os.path.dirname(PyQt5.__file__), "Qt5", "plugins", "platforms"
    )
except Exception:
    pass  # На Linux/macOS путь, как правило, задан автоматически

from PyQt5.QtWidgets import QApplication  # noqa: E402

from database import DatabaseManager      # noqa: E402
from main_window import MainWindow        # noqa: E402

# Путь к файлу базы данных в домашней директории пользователя
DB_PATH = os.path.join(os.path.expanduser("~"), "tasks.db")


def main() -> None:
    """
    Инициализирует и запускает приложение.

    Шаги выполнения:
        1. Создать экземпляр QApplication.
        2. Подключиться к базе данных SQLite (или создать файл).
        3. Создать и показать главное окно.
        4. Запустить цикл обработки событий Qt.
    """
    # ── Шаг 1: Qt-приложение ─────────────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("Task Manager")
    app.setOrganizationName("RGSU Lab")

    # ── Шаг 2: База данных ───────────────────────────────────────────────────
    db = DatabaseManager(DB_PATH)

    # ── Шаг 3: Главное окно ──────────────────────────────────────────────────
    window = MainWindow(db)
    window.show()

    # ── Шаг 4: Цикл событий ──────────────────────────────────────────────────
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
