from utils.database import db

def total_amount_for_ticket(ticket_id):
    query = """
    SELECT SUM(creditamount) as total_credit
    FROM transactions
    WHERE adddescription LIKE %s
    """
    result = db.fetch_one(query, (f"%{ticket_id}%",))
    return result['total_credit'] if result and result['total_credit'] is not None else 0

