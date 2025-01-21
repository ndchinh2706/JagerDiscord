from flask import Flask, request, jsonify
import backend_misc

app = Flask(__name__)
@app.route('/event/participant', methods=['POST'])
def redeem():
    data = request.get_json()
    id = data.get('event_id')
    response = backend_misc.event_participants(id)
    return response, 200
def run_app():
    app.run(debug=True, use_reloader=False) 