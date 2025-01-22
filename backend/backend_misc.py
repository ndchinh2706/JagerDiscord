from utils.database import Database
import json

db = Database()

def event_participants(event_id):
    try:
        db.connect()        
        query = """
            SELECT u.fullname, u.student_id, p.status
            FROM participants p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.event_id = %s
            ORDER BY u.fullname
        """
        results = db.fetch_all(query, (event_id,))
        participants_list = [
            {
                "fullname": row["fullname"],
                "student_id": row["student_id"],
                "status": row["status"]
            }
            for row in results
        ]
        return json.dumps(participants_list)
    except Exception as e:
        print(e)
        return json.dumps([])
    finally:
        if db.conn:
            db.conn.close()

def event_name(event_id):
    try:
        db.connect()
        query = """
            SELECT event_name
            FROM events
            WHERE id = %s
        """
        result = db.fetch_one(query, (event_id,))
        return result["event_name"]
    except Exception as e:
        print(e)
        return ""
    finally:
        if db.conn:
            db.conn.close()