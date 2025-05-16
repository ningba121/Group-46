import sqlite3


class DatabaseInitializer:
    """Handles SQLite database connection and table creation."""

    def __init__(self, db_name="schedules.db"):
        """ Initialize the database with a given name.
        Args:
            db_name (str): The name of the database file.
        """
        self.db_name = db_name
        self.connection = None

    def connect(self):
        """Establish a connection to the SQLite database and return a cursor.
        Returns:
            cursor connected to SQLite database."""
        self.connection = sqlite3.connect(self.db_name)
        return self.connection.cursor()

    def create_tables(self):
        """
        Create the required tables if they do not already exist:
        - user: stores user credentials and metadata.
        - schedules: stores user schedule information.
        """
        cursor = self.connect()

        # Create the user table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Create the schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                user_id INTEGER NOT NULL,
                end_date_time DATETIME NOT NULL,
                alert_date_time DATETIME NOT NULL,
                is_confirm BOOL DEFAULT FALSE,
                note TEXT,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        self.connection.commit()

    def get_connection_and_cursor(self):
        """
        Get the active database connection and cursor.
        """
        if not self.connection:
            self.connect()
        return self.connection, self.connection.cursor()

    def close_connection(self):
        """Close the active database connection."""
        if self.connection:
            self.connection.close()


if __name__ == "__main__":
    # Initialize and set up the database tables
    db_initializer = DatabaseInitializer()
    db_initializer.create_tables()
    db_initializer.close_connection()
