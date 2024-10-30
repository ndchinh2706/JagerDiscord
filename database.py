import sqlite3
from constants import db_file
def setup_database():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT,
                    event_date TEXT,
                    role_id INTEGER,
                    due_date TEXT,
                    message_id INTEGER,
                    guild_id INTEGER,
                    channel_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS participants
                    (event_id INTEGER,
                    user_id INTEGER,
                    status TEXT,
                    PRIMARY KEY (event_id, user_id))''')
    conn.commit()
    conn.close()

