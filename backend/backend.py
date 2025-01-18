from flask import Flask, request, jsonify
from backend.backend_misc import *

app = Flask(__name__)
@app.route('/create_event', methods=['POST'])
def create_event():
    data = request.get_json()
    event_name = data.get('event_name')
    points = data.get('points')
    user_id = data.get('user_id')
    if (is_permitted_user(user_id)):
        event_link = create_event_key(event_name, points)
        response = {
            'event_slug': event_link,
        }
        return jsonify(response), 200
    return jsonify({}), 403
     
@app.route('/qet_qr_key', methods=['POST'])
def get_qr_key():
    data = request.get_json()
    event_id = data.get('event_id')
    user_id = data.get('user_id')
    if (is_permitted_user(user_id)):
        key = create_qr_key(event_id)
        response = {
            'event_key_content': key,
        }
        return jsonify(response), 200
    return jsonify({}), 403

@app.route('/redeem', methods=['POST'])
def redeem():
    data = request.get_json()
    key = data.get('redeemKey')
    user = data.get('user')
    status = validate_qr_key(key, user)
    if status == False:
        response = {
            'status': 'expired',
        }
        return jsonify(response), 401
    response = {
        'eventId': status[0],
        'point': status[1],
    }
    return jsonify(response), 200
def run_app():
    app.run(debug=True, use_reloader=False) 