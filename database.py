import psycopg2
from constants import DB_Name, DB_User, DB_Pass, DB_Host, DB_Port

def setup_database():
    conn = psycopg2.connect(
        dbname=DB_Name,
        user=DB_User,
        password=DB_Pass,
        host=DB_Host,  
        port=DB_Port   
    )
    
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id BIGSERIAL PRIMARY KEY,
                    event_name TEXT,
                    event_date TEXT,
                    role_id BIGINT,
                    due_date TEXT,
                    message_id BIGINT,
                    guild_id BIGINT,
                    channel_id BIGINT
                 )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
                    event_id INTEGER,
                    user_id BIGINT,
                    status VARCHAR,
                    PRIMARY KEY (event_id, user_id),
                    FOREIGN KEY (event_id) REFERENCES events(id)
                 )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS keys (
                    key VARCHAR PRIMARY KEY,
                    points INTEGER,
                    expiry_time TEXT,
                    creator_id INTEGER,
                    redeemed INTEGER
                 )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_points (
                    user_id BIGINT PRIMARY KEY,
                    points INTEGER
                 )''')
    
    conn.commit()
    conn.close()
