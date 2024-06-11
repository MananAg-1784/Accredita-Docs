
from flask import Flask, Blueprint, send_from_directory, request
import os
from flask_app.logger import logger

app = Flask(__name__, static_folder='static', template_folder='templates')

# inititialising socket -> to app
from flask_app.socket_connection import socketio
MAX_BUFFER_SIZE = 200 * 1000 * 1000  # 50 MB
socketio.init_app(app,  max_http_buffer_size=MAX_BUFFER_SIZE)

import flask_app.main_socket
import flask_app.search_socket
import flask_app.upload_socket

# initialising all the blueprints
from flask_app.routes import main
app.register_blueprint(main)

# error_handling blueprint
from flask_app.error_handling import error_handler
app.register_blueprint(error_handler)


@app.route('/static')
def send_file_data():
    file_name = request.args.get('file_name')
    # folder_name = request.args.get('folder_name')

    # Get the absolute path of the static folder
    current_working_directory = os.getcwd()
    static_folder_path = os.path.join(app.root_path, app.static_folder)
    # Convert the absolute path to a relative path
    relative_path = os.path.relpath(static_folder_path, current_working_directory)

    if file_name:
        try:
            file_name = file_name.replace('/', '')
            # folder_name = folder_name.replace('/','')
            if file_name.replace('_','').replace('.', '').replace('-','').replace(' ','').isalnum():
                if os.path.exists(os.path.join(relative_path,'assets',file_name)):
                    return send_from_directory('static/assets', file_name)
        except:
            pass
    return "Unknown File"