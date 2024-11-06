from flask import Flask, request, jsonify, send_file
import psycopg2
from constants import DB_Name, DB_User, DB_Pass, DB_Host, DB_Port, ObfuscationKey
import obfuscator
import time
from datetime import datetime, timedelta
import backend_misc
conn = psycopg2.connect(
    dbname=DB_Name,
    user=DB_User,
    password=DB_Pass,
    host=DB_Host,  
    port=DB_Port   
)

app = Flask(__name__)

@app.route('/create_event', methods=['POST'])
def create_event():
    data = request.get_json()
    event_name = data.get('event_name')
    points = data.get('points')

    event_link = backend_misc.create_event_key(event_name, points)
    response = {
        'event_slug': event_link,
    }
    return jsonify(response), 200
    
@app.route('/get_key_content', methods=['POST'])
def get_key_content():
    data = request.get_json()
    event_id = data.get('event_id')
    key = backend_misc.create_key(event_id)
    response = {
        'event_key_content': key,
    }
    return jsonify(response), 200
