import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import uuid
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

def create_flask_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

    token_store = {}
    task_queue = []

    SITE_KEY = os.environ.get("HCAP_SITE_KEY", "f06e6c50-85a8-45c8-87d0-21a2b65856fe")

    @app.route('/')
    def index():
        return render_template('index.html', site_key=SITE_KEY)

    @app.route('/generate-token', methods=['GET'])
    def generate_token():
        task_id = str(uuid.uuid4())
        task_queue.append(task_id)
        socketio.emit('harvest_token', {'task_id': task_id})
        print(f"🚀 Task {task_id} sent to harvester")
        return jsonify({"status": "ok", "task_id": task_id})

    @app.after_request
    def set_headers(response):
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.route('/token', methods=['POST'])
    def token_received():
        data = request.json or {}
        token = data.get('token')
        task_id = data.get('task_id')
        if token and task_id:
            token_store[task_id] = {
                "token": token,
                "timestamp": datetime.utcnow().isoformat()
            }
            print(f"✅ Token saved for {task_id}: {token}")
            return jsonify({"status": "ok"})
        return jsonify({"status": "error", "message": "Missing token or task_id"}), 400

    @app.route('/get-token/<task_id>', methods=['GET'])
    def get_token(task_id):
        token_data = token_store.get(task_id)
        if token_data:
            return jsonify(token_data)
        return jsonify({"token": None, "message": "Token not ready"}), 404

    @socketio.on('request_task')
    def assign_task():
        if task_queue:
            task_id = task_queue.pop(0)
            emit('assign_task', {'task_id': task_id})
        else:
            emit('assign_task', {'task_id': None})

    @socketio.on('submit_token')
    def handle_submit_token(data):
        token = data.get('token')
        task_id = data.get('task_id')
        if token and task_id:
            token_store[task_id] = {
                "token": token,
                "timestamp": datetime.utcnow().isoformat()
            }
            print(f"✅ Token submitted and saved for task {task_id}: {token}")
        else:
            print("⚠️ Invalid token submission")

    return app, socketio


if __name__ == '__main__':
    import eventlet
    import eventlet.wsgi

    port = int(os.environ.get('PORT', 5000))
    app, socketio = create_flask_app()

    print(f"Starting server on port {port}")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', port)), app)
