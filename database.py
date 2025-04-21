import sqlite3
from typing import Tuple

class DatabaseHandler:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._connection = None

    @property
    def connection(self):
        if not self._connection:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def create_task_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            due_date TEXT NOT NULL,
            course TEXT,
            priority TEXT CHECK(priority IN ('Low', 'Medium', 'High'))
        )
        """
        self.connection.execute(query)
        self.connection.commit()

    def insert_task(self, task_data: Tuple) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO tasks (name, due_date, course, priority) VALUES (?, ?, ?, ?)",
            task_data
        )
        self.connection.commit()
        return cursor.lastrowid
