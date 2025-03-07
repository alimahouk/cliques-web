import json

from app import models
from app.constants import MessageType, PresenceError, ProtocolKey, UserPresence
from controllers import messaging


def record_make(userID):
        models.UserPresence.make(userID, UserPresence.OFFLINE)


def user_offline(userID):
        models.UserPresence.update(userID, UserPresence.OFFLINE)


def user_online(userID):
        models.UserPresence.update(userID, UserPresence.ONLINE)
