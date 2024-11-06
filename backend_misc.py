import obfuscator   
from datetime import datetime, timedelta
import psycopg2
from constants import ObfuscationKey, DB_Name, DB_User, DB_Pass, DB_Host, DB_Port

conn = psycopg2.connect(
    dbname=DB_Name,
    user=DB_User,
    password=DB_Pass,
    host=DB_Host,  
    port=DB_Port   
)

def check_expire(current_time, key_time):
    new_time = key_time + timedelta(seconds=5)
    print("Key time:" + datetime.strftime(key_time, "%Y-%m-%d %H:%M:%S"))
    print("Current time:", datetime.strftime(current_time,"%Y-%m-%d %H:%M:%S"))
    print("new_time:" + datetime.strftime(new_time,"%Y-%m-%d %H:%M:%S"))
    if new_time < current_time:
        return True
    else:
        return False
    
def create_key(event_id, point):
    key = obfuscator.obfuscate_string(str(event_id) + '|' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + '|' + str(point), ObfuscationKey)
    return key

def validate(key):
    data = obfuscator.deobfuscate_string(key, ObfuscationKey)
    event_id, key_time, point = data.split('|')
    if check_expire(datetime.now(), datetime.strptime(key_time, "%Y-%m-%d %H:%M:%S")):
        return False
     
    return event_id, point

def create_event_key(event_name, point):
    c = conn.cursor()
    query = """
        INSERT INTO events_with_points (event_name, point)
        VALUES (%s, %s)
        RETURNING id;
    """
    c.execute(query, (event_name, point))
    event_id = c.fetchone()[0]
    conn.commit()
    return event_id

def create_event_link(event_id):
    pre_link = event_id + "JagerEvent"
    link = obfuscator.obfuscate_string(pre_link, ObfuscationKey)
    return link
