import psycopg2

def setup_database():
    conn = psycopg2.connect(
        dbname="jager",
        user="postgres",
        password="postgres",
        host="localhost",  
        port="5432"   
    )
    
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_name VARCHAR,
                    event_date TEXT,
                    role_id INTEGER,
                    due_date TEXT,
                    message_id INTEGER,
                    guild_id INTEGER,
                    channel_id INTEGER
                 )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
                    event_id INTEGER,
                    user_id INTEGER,
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
                    user_id INTEGER PRIMARY KEY,
                    points INTEGER
                 )''')
    
    conn.commit()
    conn.close()
