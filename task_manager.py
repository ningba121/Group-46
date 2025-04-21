from datetime import datetime
from typing import List
from .database import DatabaseHandler

class Task:
    def __init__(self, name: str, due_date: str, course: str, priority: str):
        self.name = name
        self.due_date = datetime.strptime(due_date, "%Y-%m-%d")
        self.course = course
        if priority not in ['Low', 'Medium', 'High']:
            raise ValueError(f"Invalid priority: {priority}")
        self.priority = priority

    def __repr__(self):
        return f"<Task: {self.name} ({self.course})>"

class TaskManager:
    def __init__(self):
        self.db = DatabaseHandler()
        self.db.create_task_table()

    def add_task(self, task: Task) -> bool:
        try:
            task_data = (task.name, task.due_date.isoformat(), task.course, task.priority)
            self.db.insert_task(task_data)
            print(f"[DEBUG] Added task: {task.name}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add task: {str(e)}")
            return False
