from flask import session
from flask_socketio import join_room

from app.constants import ProtocolKey
from controllers import presence


def connected():
        if ProtocolKey.USER_ID in session:  # Make sure they're logged in.
                userID = session[ProtocolKey.USER_ID]
                join_room(userID)
                presence.user_online(userID)
                print(f"{userID} connected!")
                return True
        else:
                print("Unauthenticated user attempted to connect!")
                return False


def disconnected():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                presence.user_offline(userID)
                print(f"{userID} disconnected!")
        else:
                print("Client disconnected!")


def handle_message(message):
        print("")
