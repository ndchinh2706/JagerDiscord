import psycopg2
from psycopg2.extras import DictCursor
from constants import DB_CONFIG

class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=DictCursor)
            self.create_tables()
        except (Exception, psycopg2.Error) as error:
            print(error)

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(error)
            self.conn.rollback()

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except (Exception, psycopg2.Error) as error:
            print(error)
            return []

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except (Exception, psycopg2.Error) as error:
            print(error)
            return None

    def create_tables(self):
        tables = [
            '''CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                event_name VARCHAR,
                event_datetime TIMESTAMP,
                due_datetime TIMESTAMP,
                message_id BIGINT,
                guild_id BIGINT,
                channel_id BIGINT
            )''',
            '''CREATE TABLE IF NOT EXISTS event_roles (
                id SERIAL PRIMARY KEY,
                event_id INTEGER REFERENCES events(id),
                role_id BIGINT NOT NULL,
                UNIQUE(event_id, role_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS permission (
                user_id VARCHAR,
                role_id BIGINT,
                permission INTEGER
            )''',
            '''CREATE TABLE IF NOT EXISTS participants (
                event_id BIGINT,
                user_id BIGINT,
                status VARCHAR,
                PRIMARY KEY (event_id, user_id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            )''',
            '''CREATE TABLE IF NOT EXISTS transactions (
                transactionDate TIMESTAMP,
                addDescription TEXT,
                creditAmount int
            )''',
            '''CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                points INTEGER,
                fullname VARCHAR,
                student_id VARCHAR,
                permission INTEGER
            )''',
            '''CREATE TABLE IF NOT EXISTS reminders (
                event_id BIGINT,
                user_id BIGINT,
                reminder_type VARCHAR(20),
                sent_at TIMESTAMP,
                PRIMARY KEY (event_id, user_id, reminder_type)
            )''',
            '''CREATE SEQUENCE IF NOT EXISTS ticket_id_seq''',
            '''CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                ticket_id VARCHAR UNIQUE NOT NULL,
                user_id BIGINT NOT NULL,
                channel_id BIGINT,
                status VARCHAR DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                amount DECIMAL(10, 2) DEFAULT 0
            )'''
        ]
        for table in tables:
            self.execute_query(table)

db = Database()
