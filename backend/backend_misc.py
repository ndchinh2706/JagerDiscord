import backend.obfuscator as obfuscator   
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


#VALIDATING QR CODES CODES UNDER THIS LINE -------------
def check_qr_expire(current_time, key_time):
    new_time = key_time + timedelta(seconds=15)
    print("Key time:" + datetime.strftime(key_time, "%Y-%m-%d %H:%M:%S"))
    print("Current time:", datetime.strftime(current_time,"%Y-%m-%d %H:%M:%S"))
    print("new_time:" + datetime.strftime(new_time,"%Y-%m-%d %H:%M:%S"))
    if new_time < current_time:
        return True
    else:
        return False
    
def create_qr_key(event_id):
    #ma vcl deo biet loi o dau
    c = conn.cursor() # fix được thì ma vl, ui dit me quen no la cai ham`
    query = "SELECT point FROM events_with_points WHERE id = %s"
    c.execute(query, (int(event_id),))
    point = c.fetchone()
    key = obfuscator.obfuscate_string(str(event_id) + '|' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + '|' + str(point), ObfuscationKey)
    return key

def is_user_redeemed_qr_key(user, event_id):
    c = conn.cursor()
    query = "SELECT EXISTS (SELECT 1 FROM redeem_history WHERE user_id = %s AND event_id = %s);"
    c.execute(query, (user, event_id))
    status = c.fetchone()

    query = "SELECT EXISTS (SELECT 1 FROM events_with_points WHERE id = %s);"
    c.execute(query, (event_id,))
    event_status = c.fetchone()
    return status[0] and event_status[0] #check ca xem no co event that hay ko nua

def validate_qr_key(key, user_id):
    data = obfuscator.deobfuscate_string(key, ObfuscationKey)
    event_id, key_time, point = data.split('|')
    if check_qr_expire(datetime.now(), datetime.strptime(key_time, "%Y-%m-%d %H:%M:%S")):
        return False
    if is_user_redeemed_qr_key(user_id, event_id):
        return False
    c = conn.cursor()
    query = "SELECT event_name FROM events_with_points WHERE id = %s"
    c.execute(query, (int(event_id),))
    event_name = c.fetchone()
    query = "INSERT INTO user (user_id, points) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET points = user.points + %s"
    c.execute(query, (user_id, point, point))
    return event_name, point
#VALIDATING QR CODES CODES ABOVE THIS LINE -------------

#EVENT HANDLING CODES UNDER THIS LINE -------------
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

def is_permitted_user(user_id):
    c = conn.cursor()
    query = "SELECT EXISTS (SELECT 1 FROM users WHERE user_id = %s AND permission = 99);"
    c.execute(query, (user_id,))
    status = c.fetchone()
    return status[0]
#EVENT HANDLING CODES ABOVE THIS LINE -------------