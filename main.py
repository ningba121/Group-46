from gui import App
from task_manager import TaskManager

if __name__ == "__main__":
    task_manager = TaskManager()
    app = App(task_manager)
    app.run()
