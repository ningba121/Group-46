
from datetime import datetime, timedelta
import pytest
from taskwise.task_manager import Task, TaskManager

class TestTaskManager:
    """ Unit tests for TaskManager and Task classes.
    """
    def test_task_priority_validation(self):
        """ Test the priority validation for tasks.
        """
        valid_task = Task("Lab Report", "2024-05-18", "BIO 101", "Medium")
        assert valid_task.priority == "Medium"

        with pytest.raises(ValueError) as exc_info:
            Task("Invalid Task", "2024-05-01", "MATH 101", "Critical")
        assert "Invalid priority" in str(exc_info.value)

    def test_task_management_flow(self):
        """ Test the flow of adding, retrieving, and deleting tasks.
        """
        manager = TaskManager()
        test_task = Task(
            "Midterm Study", 
            (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "HIST 201", 
            "High"
        )
        add_result = manager.add_task(test_task)
        assert add_result is True
        upcoming = manager.get_upcoming_tasks(days=7)
        assert any(t.name == "Midterm Study" for t in upcoming)
        delete_result = manager.remove_task(1)
        assert delete_result is True



import pytest
from taskwise.database import DatabaseHandler

class TestDatabaseHandler:
    """ Unit tests for DatabaseHandler class.
    """
    def test_table_creation(self):
        """ Test the creation of the tasks table.
        """
        db = DatabaseHandler(":memory:")
        db.create_task_table()
        cursor = db.connection.cursor()
        table_count = cursor.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='tasks'"
        ).fetchone()[0]
        assert table_count == 1
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        expected_columns = ["id", "name", "due_date", "course", "priority"]
        assert columns == expected_columns

    def test_task_insertion(self):
        """ Test inserting a task into the database.
        """
        db = DatabaseHandler(":memory:")
        db.create_task_table()
        test_task = ("Final Exam Prep", "2024-05-25", "CHEM 101", "High")
        inserted_id = db.insert_task(test_task)
        cursor = db.connection.execute("SELECT * FROM tasks WHERE id=?", (inserted_id,))
        result = cursor.fetchone()
        assert result["name"] == test_task[0]
        assert result["priority"] == test_task[3]



from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytest
from taskwise.task_manager import Task
from taskwise.reminder_system import Reminder

class TestReminderSystem:
    """ Unit tests for Reminder system.
    """
    @patch("taskwise.reminder_system.smtplib.SMTP")
    def test_email_notification(self, mock_smtp):
        """ Test the email notification system.
        """
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        future_date = (datetime.now() + timedelta(hours=36)).strftime("%Y-%m-%d")
        task = Task("Project Deadline", future_date, "CS 101", "High")
        reminder = Reminder()
        reminder.send_email_alert(task)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called()
        mock_server.sendmail.assert_called_once()

    def test_past_due_reminder(self):
        """ Test the reminder for a task that is past the due date.
        """
        reminder = Reminder()
        expired_task = Task("Late Submission", "2023-11-01", "PHYS 102", "Medium")
        with pytest.raises(ValueError) as exc_info:
            reminder.schedule_reminder(expired_task)
        assert "past due date" in str(exc_info.value).lower()



from taskwise.collaboration import GroupProject
from taskwise.task_manager import Task

class TestCollaboration:
    """ Unit tests for Collaboration class.
    """
    def test_group_task_assignment(self):
        """ Test the assignment of tasks to group members.
        """
        project = GroupProject(project_id=1001, project_name="AI Research Paper")
        task = Task("Literature Review", "2024-06-15", "CS 505", "High")
        project.assign_task(task, "john.doe@university.edu")
        assert len(project.assigned_tasks) == 1
        assignment = project.assigned_tasks[0]
        assert assignment["task"].name == "Literature Review"
        assert assignment["assignee"] == "john.doe@university.edu"

    def test_progress_tracking(self):
        """ Test the progress tracking of group tasks.
        """
        project = GroupProject(project_id=1002, project_name="Chemistry Lab")
        tasks = [
            Task("Experiment Setup", "2024-05-20", "CHEM 201", "Medium"),
            Task("Data Analysis", "2024-05-25", "CHEM 201", "High")
        ]
        for task in tasks:
            project.assign_task(task, "lab.team@university.edu")
        project.assigned_tasks[0]["status"] = "completed"
        progress = project.sync_progress()
        assert progress["total_tasks"] == 2
        assert progress["completed"] == 1
        assert progress["pending"] == 1
