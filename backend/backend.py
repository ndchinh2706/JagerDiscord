from flask import Flask, render_template, jsonify
from backend.backend_misc import event_participants, event_name
from flask_cors import CORS
app = Flask(__name__)
 
CORS(app)
@app.route('/event/participant/<int:id>', methods=['GET'])
def get_event_participants(id):
    try:
        result = event_participants(id)
        name = event_name(id)
        return jsonify({"success": True, "data": result, "event_name": name}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": "Failed rui nek"}), 500

#qua luoi lam 1 project moi nen nen bo may render html thang tu backend luon dcmm nhu nao
@app.route('/event/<int:id>')
def event(id):
    name = event_name(id)
    return render_template('event.html', event_id=id, event_name=name)

if __name__ == '__main__':
    app.run(debug=True)
