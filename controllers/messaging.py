import datetime
import json
import uuid

from flask_socketio import emit

from app.constants import MessageType, ProtocolKey


# json.dumps() chokes on datetime objects. This function 
# converts them into strings.
def serialisation_defaults(obj):
        if isinstance(obj, datetime.datetime):
                return obj.astimezone().isoformat()
        elif isinstance(obj, uuid.UUID):
                return str(obj)
        else:
                return super().default(obj)


class SHMessage():
        def __init__(self):
                self.body = dict()
                self.errorCode = 0
                self.type = MessageType.UNDEFINED

        def serialise(self):
                message = dict()
                message[ProtocolKey.MESSAGE_TYPE] = self.type
                message[ProtocolKey.ERR_CODE] = self.errorCode
                message[ProtocolKey.MESSAGE_BODY] = self.body
                return json.dumps(message, default=serialisation_defaults)

def send(message, room=None):
        emit("message", message.serialise(), namespace="/", room=room)
