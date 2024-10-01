import threading
import os, time, starlink_grpc
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
from flask_login import LoginManager

from database import get_db, init_db
from routing import routing
from starlink import fetch_current_data, get_starlink_inital_data
from user import User

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
DATABASE = "users.db"
init_db(app, DATABASE)
routing(app, DATABASE)


@login_manager.user_loader
def load_user(user_id):
    db = get_db(DATABASE)
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(user["id"], user["username"], user["password"]) if user else None


def background_data_fetch():
    while True:
        data = fetch_current_data()
        socketio.emit("data_update", data)
        time.sleep(3)


def start_background_data_fetch():
    thread = threading.Thread(target=background_data_fetch)
    thread.daemon = (
        True  # Allow thread to exit even if the main program is still running
    )
    thread.start()


@socketio.on("dishy_event")
def handle_message(data):
    if data == "reboot":
        starlink_grpc.reboot()
    elif data == "stow":
        starlink_grpc.set_stow_state(unstow=False)
    elif data == "unstow":
        starlink_grpc.set_stow_state(unstow=True)
    print(data)


if __name__ == "__main__":
    start_background_data_fetch()
    socketio.run(app, debug=True, host="0.0.0.0", port=80)
