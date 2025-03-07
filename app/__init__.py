import os

from flask import Flask, session
from flask_mail import Mail
from flask_session import Session
from flask_socketio import SocketIO
from werkzeug.contrib.fixers import ProxyFix

from app import config

app = Flask(__name__)

# Flask Configuration
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SESSION_TYPE"] = config.SESSION_TYPE
app.config["PERMANENT_SESSION_LIFETIME"] = config.PERMANENT_SESSION_LIFETIME
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = config.SEND_FILE_MAX_AGE_DEFAULT
app.config["PREFERRED_URL_SCHEME"] = config.APP_SCHEME

# Mail Configuration
app.config["MAIL_DEFAULT_SENDER"] = config.MAIL_DEFAULT_SENDER
app.config["MAIL_USE_TLS"] = config.MAIL_USE_TLS
app.config["MAIL_USERNAME"] = config.MAIL_USERNAME
app.config["MAIL_PASSWORD"] = config.MAIL_PASSWORD
app.config["MAIL_HOST"] = config.MAIL_HOST

# Enable template auto-reload in development
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.wsgi_app = ProxyFix(app.wsgi_app)  # This fixes issues when running behind Nginx as a proxy.

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

mail = Mail(app)
Session(app)
socketio = SocketIO(app)

from app import routes

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
