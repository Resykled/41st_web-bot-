import sqlite3
import os
from datetime import datetime

DB_FILE = os.getenv('DB_FILE', 'attendance.db')

def get_db_connection():
    """Creates and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    return conn
def add_columns():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Füge die neuen Spalten hinzu
    try:
        cursor.execute("ALTER TABLE Raids ADD COLUMN total_attendees INTEGER DEFAULT 0;")
        cursor.execute("ALTER TABLE Raids ADD COLUMN total_attendance INTEGER DEFAULT 0;")
        print("Spalten erfolgreich hinzugefügt.")
    except sqlite3.OperationalError as e:
        print(f"Fehler: {e}")

    conn.commit()
    conn.close()

add_columns()

def initialize_database():
    """Creates the required tables if they do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            all_time_attendance INTEGER DEFAULT 0,
            all_time_host_count INTEGER DEFAULT 0,
            current_attendance INTEGER DEFAULT 0,
            current_host_count INTEGER DEFAULT 0
        );
    ''')

    # 2. Raids Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Raids (
            raid_id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_user_id TEXT,
            raid_type TEXT,
            platform TEXT,
            game TEXT,
            date_of_raid TEXT,
            total_attendees INTEGER DEFAULT 0,
            total_attendance INTEGER DEFAULT 0,
            FOREIGN KEY (host_user_id) REFERENCES Users(user_id)
        );
    ''')

    # 3. Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            raid_id INTEGER,
            attendance_points INTEGER,
            date_recorded TEXT,
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (raid_id) REFERENCES Raids(raid_id)
        );
    ''')

    conn.commit()
    conn.close()

def ensure_user_exists(user_id, username=None):
    """Ensures a user row exists in the database, inserts if not found."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        cursor.execute(
            "INSERT INTO Users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        conn.commit()
    conn.close()

def record_raid(host_id, host_username, raid_type, platform, game, date_str):
    """
    Inserts a new raid record into the Raids table.
    Returns the newly created raid_id.
    """
    ensure_user_exists(host_id, host_username)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert raid data
    cursor.execute(
        """
        INSERT INTO Raids (host_user_id, raid_type, platform, game, date_of_raid)
        VALUES (?, ?, ?, ?, ?)
        """,
        (host_id, raid_type, platform, game, date_str)
    )
    raid_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return raid_id

def record_attendance(user_id, username, raid_id, attendance_points, date_str):
    """
    Creates a record in Attendance table and updates current_attendance in Users.
    """
    ensure_user_exists(user_id, username)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert into Attendance table
    cursor.execute(
        """
        INSERT INTO Attendance (user_id, raid_id, attendance_points, date_recorded)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, raid_id, attendance_points, date_str)
    )

    # Update user's current attendance
    cursor.execute(
        """
        UPDATE Users
        SET current_attendance = current_attendance + ?
        WHERE user_id = ?
        """,
        (attendance_points, user_id)
    )

    conn.commit()
    conn.close()

def update_raid_stats(raid_id, total_attendees, total_attendance):
    """Updates the stats for a specific raid."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Raids
        SET total_attendees = ?, total_attendance = ?
        WHERE raid_id = ?
        """,
        (total_attendees, total_attendance, raid_id)
    )
    conn.commit()
    conn.close()

def get_raid_statistics():
    """
    Retrieves raid statistics grouped by game and raid type.
    Returns: (raid_data, top_raid_type)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to get attendance grouped by game and raid type
    cursor.execute(
        """
        SELECT TRIM(LOWER(game)) as normalized_game, raid_type, SUM(attendance_points) as attendance
        FROM Raids
        LEFT JOIN Attendance ON Raids.raid_id = Attendance.raid_id
        GROUP BY normalized_game, raid_type
        """
    )
    rows = cursor.fetchall()

    # Build the raid_data dictionary
    raid_data = {}
    for row in rows:
        game = row[0].strip().capitalize()  # Ensure no leading/trailing spaces and proper capitalization

        raid_type = row[1]
        attendance = row[2]

        if game not in raid_data:
            raid_data[game] = {"total": 0}
        raid_data[game]["total"] += attendance
        raid_data[game][raid_type] = attendance

    # Query to find the most used raid type
    cursor.execute(
        """
        SELECT raid_type, COUNT(*) as count
        FROM Raids
        GROUP BY raid_type
        ORDER BY count DESC
        LIMIT 1
        """
    )
    top_raid_type = cursor.fetchone()

    conn.close()
    return raid_data, top_raid_type



def reset_database():
    """
    Drops all tables and recreates them, effectively wiping all data.
    Useful for testing or starting fresh.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop tables if they exist
    cursor.execute("DROP TABLE IF EXISTS Attendance;")
    cursor.execute("DROP TABLE IF EXISTS Raids;")
    cursor.execute("DROP TABLE IF EXISTS Users;")

    conn.commit()
    conn.close()

    # Re-initialize to recreate the tables
    initialize_database()

def finalize_two_week_cycle():
    """
    Adds current attendance/host counts to all_time columns, then resets current columns to 0.
    This simulates the end-of-cycle 'reset' logic.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Add current attendance/host to all-time, then reset current columns to zero
    cursor.execute(
        """
        UPDATE Users
        SET
            all_time_attendance = all_time_attendance + current_attendance,
            all_time_host_count = all_time_host_count + current_host_count,
            current_attendance = 0,
            current_host_count = 0
        """
    )

    conn.commit()
    conn.close()

def record_host_points(host_id, host_points):
    """
    Updates the current_host_count for the host in the Users table.
    """
    ensure_user_exists(host_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE Users
        SET current_host_count = current_host_count + ?
        WHERE user_id = ?
        """,
        (host_points, host_id)
    )

    conn.commit()
    conn.close()

def get_user_attendance(user_id):
    """
    Retrieves a user's current and all-time attendance from the database.
    Returns a tuple: (current_attendance, current_host_count, all_time_attendance, all_time_host_count).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT current_attendance, current_host_count, all_time_attendance, all_time_host_count
        FROM Users
        WHERE user_id = ?
        """,
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return row  # Tuple of 4: (current_att, current_host, all_time_att, all_time_host)
    else:
        return None
