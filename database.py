import psycopg2
from constants import Discord_API_KEY_bot, DB_Name, DB_User, DB_Pass, DB_Host, DB_Port

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
                  id SERIAL PRIMARY KEY,
                  event_name VARCHAR,
                  event_date TEXT,
                  role_id INTEGER,
                  due_date TEXT,
                  message_id INTEGER,
                  guild_id INTEGER,
                  channel_id INTEGER
               )''')
   c.execute('''CREATE TABLE IF NOT EXISTS events_with_points (
                  id SERIAL PRIMARY KEY,
                  event_name VARCHAR,
                  point INTEGER)''')
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
   c.execute('''CREATE TABLE IF NOT EXISTS redeem_history (
            user_id INTEGER PRIMARY KEY,
            event_id INTEGER
         )''')
   conn.commit()
   conn.close()
setup_database()