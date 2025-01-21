from restructure.utils.database import Database as db
import json

def event_participants(event_id):
    try:
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
        print(f"Error getting participants: {e}")
        return json.dumps([])    
