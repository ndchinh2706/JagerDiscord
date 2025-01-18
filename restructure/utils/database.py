# utils/database.py

import psycopg2
from psycopg2.extras import DictCursor
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=DictCursor)
            print("Database connection successful")
            self.create_tables()
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)

    def disconnect(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            print("Database connection closed")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print("Error executing query:", error)
            self.conn.rollback()

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except (Exception, psycopg2.Error) as error:
            print("Error fetching data:", error)
            return []

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except (Exception, psycopg2.Error) as error:
            print("Error fetching data:", error)
            return None

    def create_tables(self):
        tables = [
            '''CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                event_name VARCHAR,
                event_datetime TIMESTAMP,
                role_id BIGINT,
                due_datetime TIMESTAMP,
                message_id BIGINT,
                guild_id BIGINT,
                channel_id BIGINT
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
            )'''
        ]

        for table in tables:
            self.execute_query(table)
        
        print("All tables created successfully")

db = Database()