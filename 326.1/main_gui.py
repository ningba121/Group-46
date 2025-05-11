import queue
import sys
import sqlite3
from datetime import datetime
import pyttsx3
from PyQt5.QtCore import QDateTime, Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLineEdit, QDialog, QDialogButtonBox, QLabel, QComboBox,
    QDateTimeEdit, QFileDialog, QMessageBox, QAbstractItemView, QSystemTrayIcon
)
from style import get_dark_theme, get_light_theme


class TTSThread(QThread):
    """Thread for handling text-to-speech (TTS) operations."""

    speak_signal = pyqtSignal(str)

    def __init__(self):
        """Initialize the TTS thread, set up speech engine, and configure the voice."""
        super().__init__()
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'english' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.queue = queue.Queue()
        self.running = True
        self.interrupt = False

    def run(self):
        """Run the TTS engine in a loop, processing messages in the queue."""
        while self.running:
            message = self.queue.get()
            if message is None:
                break
            if self.interrupt:
                self.queue.task_done()
                continue
            self.engine.say(message)
            self.engine.runAndWait()
            self.queue.task_done()

    def stop(self):
        """Stop the TTS thread and clear the message queue."""
        self.running = False
        self.clear_queue()
        self.queue.put(None)

    def speak(self, message):
        """Put a message into the queue for TTS processing."""
        self.queue.put(message)

    def clear_queue(self):
        """Clear the message queue."""
        with self.queue.mutex:
            self.queue.queue.clear()

    def toggle_interrupt(self, status: bool):
        """Toggle interruption of the TTS engine."""
        self.interrupt = status
        if status:
            self.engine.stop()
            self.clear_queue()



class ScheduleApp(QWidget):
    """Main application for managing schedules and user interactions."""

    def __init__(self, user):
        """Initialize the ScheduleApp window and set up necessary components."""
        super().__init__()
        self.user = user
        self.uid = user[0]
        self.setWindowTitle("Schedule Manager")
        self.setGeometry(300, 100, 1200, 800)
        self.use_dark_theme = False
        self.conn = sqlite3.connect('schedules.db')
        self.cursor = self.conn.cursor()
        self.tts = TTSThread()
        self.tts.start()
        self.tray_icon = QSystemTrayIcon()
        self.icon = QIcon("icon.png")
        self.tray_icon.setIcon(self.icon)
        self.tray_icon.setToolTip("Schedule Manager")
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
        self.blink_state = False
        self.alerted_ids = set()
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_alerts)
        self.poll_timer.start(2000)
        self.icon_1 = QIcon("info_r.png")
        self.icon_2 = QIcon("info_b.png")
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_tray)

    def on_tray_icon_activated(self, reason):
        """Handle the tray icon activation event."""
        if reason == QSystemTrayIcon.Trigger:
            self.show()
            self.blink_timer.stop()
            self.tray_icon.setIcon(self.icon)
            self.raise_()
            self.activateWindow()

    def check_alerts(self):
        """Check and handle schedule alerts."""
        now = datetime.now().isoformat(sep='T')
        params = [self.uid, now] + list(self.alerted_ids) if self.alerted_ids else [self.uid, now]
        placeholder = ','.join(['?'] * len(self.alerted_ids)) if self.alerted_ids else '0'

        self.cursor.execute(
            f"SELECT id, title FROM schedules WHERE user_id=? AND is_confirm=0 "
            f"AND alert_date_time<=? AND id NOT IN ({placeholder})", params
        )
        rows = self.cursor.fetchall()
        if not rows:
            return

        titles = [row[1] for row in rows]
        ids = [row[0] for row in rows]
        self.alerted_ids.update(ids)
        message = "; ".join(f"{t} has reached its alert time" for t in titles)
        self.tts.speak(message)
        self.tooltip_text = message
        self.tray_icon.setToolTip(message)
        self.blink_timer.start(500)
        QMessageBox.information(self, "Reminder", message)
        self.blink_timer.stop()
        self.tray_icon.setIcon(self.icon)

    def blink_tray(self):
        """Blink the system tray icon as a reminder."""
        self.blink_state = not self.blink_state
        self.tray_icon.setIcon(self.icon_1 if self.blink_state else self.icon_2)

    def stop(self):
        """Stop the timers and TTS thread."""
        self.poll_timer.stop()
        self.blink_timer.stop()
        self.tts.stop()

    def initUI(self):
        """Initialize the UI components, including theme, toolbar, and schedule table."""
        if self.use_dark_theme:
            self.setStyleSheet(get_dark_theme())
        else:
            self.setStyleSheet(get_light_theme())
        layout = QVBoxLayout()

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search… title or note")
        self.search_edit.textChanged.connect(self.reload_table)
        toolbar.addWidget(self.search_edit)

        self.date_from = QDateTimeEdit(calendarPopup=True)
        self.date_from.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.date_from.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_to = QDateTimeEdit(calendarPopup=True)
        self.date_to.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_to.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.date_from.dateTimeChanged.connect(self.reload_table)
        self.date_to.dateTimeChanged.connect(self.reload_table)
        toolbar.addWidget(QLabel("From"))
        toolbar.addWidget(self.date_from)
        toolbar.addWidget(QLabel("To"))
        toolbar.addWidget(self.date_to)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(lambda: self.open_dialog())
        toolbar.addWidget(self.add_button)

        self.export_button = QPushButton("Export CSV")
        self.export_button.clicked.connect(self.export_data)
        toolbar.addWidget(self.export_button)

        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Title", "End Time", "Alert Time", "Status", "Note", "Created", "Actions"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 200)
        self.table.setColumnWidth(6, 240)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.reload_table()

    def reload_table(self):
        """Reload the schedule table based on the search criteria and date range."""
        kw = self.search_edit.text()
        df = self.date_from.dateTime().toString(Qt.ISODate)
        dt = self.date_to.dateTime().toString(Qt.ISODate)
        sql = '''
            SELECT id, title, end_date_time, alert_date_time, is_confirm, note, create_time
            FROM schedules
            WHERE user_id=? AND (title LIKE ? OR note LIKE ?) AND end_date_time BETWEEN ? AND ?
            ORDER BY end_date_time
        '''
        params = (self.uid, f'%{kw}%', f'%{kw}%', df, dt)
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()

        self.table.setRowCount(len(rows))
        for i, (sid, title, end, alert, conf, note, created) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(title))
            self.table.setItem(i, 1, QTableWidgetItem(end))
            self.table.setItem(i, 2, QTableWidgetItem(alert))
            self.table.setItem(i, 3, QTableWidgetItem('Confirmed' if conf else 'Unconfirmed'))
            self.table.setItem(i, 4, QTableWidgetItem(note))
            self.table.setItem(i, 5, QTableWidgetItem(created))
            w = QWidget()
            hb = QHBoxLayout(w)
            for lbl, fn in [('Edit', self.open_dialog), ('Delete', self.delete_by_id), ('Confirm', self.confirm_by_id)]:
                btn = QPushButton(lbl)
                btn.clicked.connect(lambda _, f=fn, x=sid: f(x))
                hb.addWidget(btn)
            hb.setContentsMargins(0,0,0,0)
            self.table.setCellWidget(i, 6, w)

    def open_dialog(self, sid=None):
        """Open the dialog for adding or editing a schedule."""
        dlg = AddEditDialog(self, sid, self.use_dark_theme)
        if dlg.exec_() == QDialog.Accepted:
            title, end, alert, note, conf = dlg.get_data()
            if QDateTime.fromString(alert, Qt.ISODate) > QDateTime.fromString(end, Qt.ISODate):
                QMessageBox.warning(self, "Invalid", "Alert cannot be after End.")
                return
            if sid:
                self.cursor.execute(
                    "UPDATE schedules SET title=?, end_date_time=?, alert_date_time=?, note=?, is_confirm=? WHERE id=?",
                    (title, end, alert, note, conf, sid)
                )
            else:
                self.cursor.execute(
                    "INSERT INTO schedules (title, user_id, end_date_time, alert_date_time, is_confirm, note) VALUES (?,?,?,?,?,?)",
                    (title, self.uid, end, alert, conf, note)
                )
            self.conn.commit()
            self.reload_table()

    def delete_by_id(self, sid):
        """Delete a schedule by its ID."""
        self.cursor.execute("DELETE FROM schedules WHERE id=?", (sid,))
        self.conn.commit()
        self.reload_table()

    def confirm_by_id(self, sid):
        """Mark a schedule as confirmed by its ID."""
        self.cursor.execute("UPDATE schedules SET is_confirm=1 WHERE id=?", (sid,))
        self.conn.commit()
        self.reload_table()

    def export_data(self):
        """Export the user's schedule data to a CSV file."""
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", filter="*.csv")
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                self.cursor.execute(
                    "SELECT title, end_date_time, alert_date_time, is_confirm, note, create_time FROM schedules WHERE user_id=?",
                    (self.uid,)
                )
                f.write('Title,End,Alert,Status,Note,Created\n')
                for row in self.cursor.fetchall():
                    status = 'Confirmed' if row[3] else 'Unconfirmed'
                    line = [row[0], row[1], row[2], status, row[4], row[5]]
                    f.write(','.join(line) + '\n')
            QMessageBox.information(self, "Export", "Exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class AddEditDialog(QDialog):
    """Dialog for adding or editing a schedule entry."""

    def __init__(self, parent=None, sid=None, use_dark_theme=False):
        """Initialize the dialog with schedule data if editing an existing entry."""
        super().__init__(parent)
        self.sid = sid
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Edit" if sid else "Add New")
        self.setFixedSize(360, 380)
        if use_dark_theme:
            self.setStyleSheet(get_dark_theme())
        else:
            self.setStyleSheet(get_light_theme())

        lo = QVBoxLayout(self)
        lo.addWidget(QLabel("Title"))
        self.title_edit = QLineEdit(self)
        lo.addWidget(self.title_edit)

        lo.addWidget(QLabel("End DateTime"))
        self.end_edit = QDateTimeEdit(QDateTime.currentDateTime(), self)
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        lo.addWidget(self.end_edit)

        lo.addWidget(QLabel("Alert DateTime"))
        self.alert_edit = QDateTimeEdit(QDateTime.currentDateTime(), self)
        self.alert_edit.setCalendarPopup(True)
        self.alert_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        lo.addWidget(self.alert_edit)

        lo.addWidget(QLabel("Note"))
        self.note_edit = QLineEdit(self)
        lo.addWidget(self.note_edit)

        if sid:
            lo.addWidget(QLabel("Status"))
            self.status_combo = QComboBox(self)
            self.status_combo.addItems(['Unconfirmed', 'Confirmed'])
            lo.addWidget(self.status_combo)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lo.addWidget(bb)

        if sid:
            c = parent.cursor
            c.execute("SELECT title,end_date_time,alert_date_time,note,is_confirm FROM schedules WHERE id=?", (sid,))
            title, end, alert, note, conf = c.fetchone()
            self.title_edit.setText(title)
            self.end_edit.setDateTime(QDateTime.fromString(end, Qt.ISODate))
            self.alert_edit.setDateTime(QDateTime.fromString(alert, Qt.ISODate))
            self.note_edit.setText(note)
            self.status_combo.setCurrentIndex(1 if conf else 0)

    def get_data(self):
        """Retrieve and validate data from the input fields."""
        title = self.title_edit.text().strip()
        end = self.end_edit.dateTime().toString(Qt.ISODate)
        alert = self.alert_edit.dateTime().toString(Qt.ISODate)
        note = self.note_edit.text().strip()
        conf = 1 if (hasattr(self, 'status_combo') and self.status_combo.currentText() == 'Confirmed') else 0

        # Validation: Both alert and end times must be after current time
        current_time = QDateTime.currentDateTime().toString(Qt.ISODate)
        if QDateTime.fromString(alert, Qt.ISODate) <= QDateTime.fromString(current_time, Qt.ISODate):
            QMessageBox.warning(self, "Invalid Time", "Alert time must be in the future.")
            return None
        if QDateTime.fromString(end, Qt.ISODate) <= QDateTime.fromString(current_time, Qt.ISODate):
            QMessageBox.warning(self, "Invalid Time", "End time must be in the future.")
            return None
        if QDateTime.fromString(alert, Qt.ISODate) > QDateTime.fromString(end, Qt.ISODate):
            QMessageBox.warning(self, "Invalid Time", "Alert time cannot be after End time.")
            return None

        return title, end, alert, note, conf

    def accept(self):
        data = self.get_data()
        if data:
            super().accept()


if __name__ == '__main__':
    demo_user = (1, '123@qwe.cc')
    app = QApplication(sys.argv)
    win = ScheduleApp(demo_user)
    win.initUI()
    win.show()
    sys.exit(app.exec_())
