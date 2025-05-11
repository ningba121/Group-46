"""
style.py

This module provides functions that return Qt-compatible style sheets (QSS)
for light and dark themes. The styles affect the appearance of common widgets
such as QWidget, QPushButton, QTableWidget, and form elements.
"""

def get_light_theme():
    """Return the light theme style sheet as a string."""
    return """
    QWidget {
        background-color: #f9f9f9;
        font-family: "Helvetica Neue", "Segoe UI", "Microsoft YaHei", sans-serif;
        font-size: 14px;
        color: #2c2c2c;
    }

    QPushButton {
        background-color: #f77f6e;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 5px 8px;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #e06756;
    }

    QPushButton:pressed {
        background-color: #c45445;
    }

    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        gridline-color: #efefef;
        selection-background-color: #fdecea;
        selection-color: #2c2c2c;
        alternate-background-color: #fdfdfd;
    }

    QHeaderView::section {
        background-color: #e0e0e0;
        color: #222;
        padding: 6px;
        border: none;
        font-weight: bold;
        text-align: left;
    }

    QLineEdit, QDateTimeEdit, QComboBox {
        padding: 6px;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 14px;
    }
    """


def get_dark_theme():
    """Return the dark theme style sheet as a string."""
    return """
    QWidget {
        background-color: #121212;
        font-family: "Helvetica Neue", "Segoe UI", "Microsoft YaHei", sans-serif;
        font-size: 14px;
        color: #e0e0e0;
    }

    QPushButton {
        background-color: #bb86fc;
        color: black;
        border: none;
        border-radius: 8px;
        padding: 5px 8px;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #9f6dfc;
    }

    QPushButton:pressed {
        background-color: #7c4dff;
    }

    QTableWidget {
        background-color: #1e1e1e;
        border: 1px solid #333;
        gridline-color: #2e2e2e;
        selection-background-color: #3700b3;
        selection-color: #ffffff;
        alternate-background-color: #222;
    }

    QHeaderView::section {
        background-color: #2a2a2a;
        color: #ccc;
        padding: 6px;
        border: none;
        font-weight: bold;
        text-align: left;
    }

    QLineEdit, QDateTimeEdit, QComboBox {
        padding: 6px;
        border: 1px solid #444;
        border-radius: 4px;
        font-size: 14px;
        background-color: #2c2c2c;
        color: #fff;
    }
    """
