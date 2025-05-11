import hashlib
import re
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFormLayout, QHBoxLayout, QMessageBox, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from main_gui import ScheduleApp


def get_db_connection():
    """Establishes a connection to the local SQLite database."""
    return sqlite3.connect("schedules.db")


class LoginWindow(QWidget):
    """The main login window for user authentication."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Schedule Manager')
        self.setFixedSize(400, 300)
        self.init_ui()

    def init_ui(self):
        """Initializes the UI components of the login window."""
        self.setStyleSheet("background-color: #ecf0f1;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # Title label
        title_label = QLabel("User Login")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        main_layout.addWidget(title_label)

        # Form layout for inputs
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setVerticalSpacing(15)

        input_style = """
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your email")
        self.username_input.setFixedHeight(35)
        self.username_input.setStyleSheet(input_style)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(35)
        self.password_input.setStyleSheet(input_style)

        form_layout.addRow("Email:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        main_layout.addLayout(form_layout)

        # Dark mode toggle
        self.dark_mode_checkbox = QCheckBox("Enable dark mode")
        self.dark_mode_checkbox.setStyleSheet("font-size: 13px;")
        main_layout.addWidget(self.dark_mode_checkbox)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        login_btn = QPushButton("Login")
        login_btn.setFixedHeight(35)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        login_btn.clicked.connect(self.login)

        register_btn = QPushButton("Register")
        register_btn.setFixedHeight(35)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        register_btn.clicked.connect(self.open_register)

        button_layout.addWidget(login_btn)
        button_layout.addWidget(register_btn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def hash_password(self, password):
        """Hashes the password with a predefined salt using SHA256."""
        salt = "mysalt12$%&^3"
        return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

    def open_register(self):
        """Opens the registration dialog."""
        dialog = RegisterDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Registration successful. Please log in.")

    def login(self):
        """Validates user credentials and launches the main schedule application if successful."""
        email = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Email and password cannot be empty.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email FROM user WHERE email=? AND password_hash=?",
            (email, self.hash_password(password))
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            QMessageBox.information(self, "Login", "Login successful!")
            main_win = ScheduleApp(user)
            main_win.use_dark_theme = self.dark_mode_checkbox.isChecked()
            main_win.initUI()
            self.hide()
            main_win.show()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect email or password.")


class RegisterDialog(QDialog):
    """Registration dialog for new users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Register New User")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #ecf0f1;")
        self.init_ui()

    def init_ui(self):
        """Initializes the UI components of the registration form."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        title_label = QLabel("Create Account")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setVerticalSpacing(15)

        input_style = """
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.email_input.setFixedHeight(35)
        self.email_input.setStyleSheet(input_style)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(35)
        self.password_input.setStyleSheet(input_style)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setFixedHeight(35)
        self.confirm_input.setStyleSheet(input_style)

        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Confirm:", self.confirm_input)
        layout.addLayout(form_layout)

        register_btn = QPushButton("Register")
        register_btn.setFixedHeight(35)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        register_btn.clicked.connect(self.register)
        layout.addWidget(register_btn)

        self.setLayout(layout)

    def is_valid_email(self, email):
        """Validates the email format using regex."""
        pattern = r'^[\w.-]+@[\w.-]+\.\w{2,4}$'
        return re.match(pattern, email) is not None

    def hash_password(self, password):
        """
        Hashes a password with a salt.
        """
        salt = "mysalt12$%&^3"
        return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

    def register(self):
        """
        Handles the user registration logic, including validation and DB insert.
        """
        email = self.email_input.text().strip()
        pwd = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()

        if not email or not pwd or not confirm:
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        if not self.is_valid_email(email):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return

        if pwd != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user WHERE email=?", (email,))
        if cursor.fetchone():
            QMessageBox.warning(self, "Registration Failed", "Email already registered.")
            conn.close()
            return

        cursor.execute("INSERT INTO user (email, password_hash) VALUES (?, ?)", (email, self.hash_password(pwd)))
        conn.commit()
        conn.close()
        self.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.png"))
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
