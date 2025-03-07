from datetime import datetime

from app import models
from app.constants import ConnectivityError, MessageType, ProtocolKey, UserConnectionStatus
from controllers import cliques, presence
from controllers.crypto import sha256_str
from controllers.messaging import SHMessage, send


def connection_exists(user1, user2):
        return models.UserConnection.exists(user1, user2)


def connection_remove(initiatorID, targetID):
        if initiatorID is None:
                raise ValueError("connectivity.connection_remove(2): initiatorID argument is null")
        if targetID is None:
                raise ValueError("connectivity.connection_remove(2): targetID argument is null")

        response = SHMessage()
        response.type = MessageType.CONNECTION_REMOVE

        if initiatorID == targetID:
                response.errorCode = ConnectivityError.RECURSIVE
        else:
                response.body[ProtocolKey.USER_ID] = targetID

                # Get the current cliques BEFORE this operation and
                # send the list relevant to every uer involved.
                newCliques = cliques.cliques_including(initiatorID, targetID)
                involvedUsers = set()
                for clique in newCliques:
                        involvedUsers.update(clique)

                cliques.cliques_break(initiatorID, targetID)
                models.UserConnection.remove(initiatorID, targetID)

                # Notify the target.
                notification = SHMessage()
                notification.type = MessageType.CONNECTION_REMOVED
                notification.body[ProtocolKey.USER_ID] = initiatorID
                send(notification, targetID)

                for user in involvedUsers:
                        userCliques = cliques.cliques_get(user)
                        notification = SHMessage()
                        notification.type = MessageType.CLIQUES_GET
                        notification.body = userCliques
                        send(notification, user)

        return response

def connections_get(userID, limit=0):
        if userID is None:
                raise ValueError("connectivity.connections_get(2): userID argument is null")
        
        return models.UserConnection.all_get(userID, limit=limit)


def invite_connection_make(userID, code):
        if userID is None:
                raise ValueError("connectivity.invite_connection_make(2): userID argument is null")
        if code is None:
                raise ValueError("connectivity.invite_connection_make(2): code argument is null")
        
        senderID = invite_link_sender(code)
        if senderID is None or senderID == userID: # User is using their own invite link; do nothing.
                return
        
        existing_connection = models.UserConnection.exists(senderID, userID)
        if existing_connection:
                return # User sent an invite to an existing connection; do nothing.
        
        models.User.referrer_update(senderID, userID)
        # This is a one-time code. It's now been used up.
        models.InviteCode.delete(code)
        models.UserConnection.make(senderID, userID, status=UserConnectionStatus.ESTABLISHED)
        cliques.cliques_make(senderID, userID)
        # Notify the inviter if they're online.
        notification = SHMessage()
        notification.type = MessageType.CONNECTION_REQUEST_ACCEPTED
        target = models.User.get(userID=userID)
        del target[ProtocolKey.PASSWORD]
        del target[ProtocolKey.SALT]
        notification.body = target
        send(notification, senderID)


def invite_link_make(userID):
        if userID is None:
                raise ValueError("connectivity.invite_link_make(1): userID argument is null")
        
        response = SHMessage()
        response.type = MessageType.INVITE_LINK
        # Hash the userID along with the current time.
        timestamp = datetime.now().astimezone().isoformat()
        code = sha256_str(str(userID) + timestamp)
        models.InviteCode.make(userID, code)

        response.body = code

        return response


def invite_link_sender(code):
        if code is None:
                raise ValueError("connectivity.invite_link_sender(1): code argument is null")

        invite = models.InviteCode.get(code=code)
        if invite is not None:
                return invite[ProtocolKey.USER_ID]
        else:
                return None


def mutual_connections(userID1, userID2):
        return models.UserConnection.mutuals(userID1, userID2)


def request_accept(initiatorID, targetID):
        if initiatorID is None:
                raise ValueError("connectivity.request_make(2): initiatorID argument is null")
        if targetID is None:
                raise ValueError("connectivity.request_make(2): targetID argument is null")
        
        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUEST_ACCEPT

        if initiatorID == targetID:
                response.errorCode = ConnectivityError.RECURSIVE
        else:
                models.UserConnection.accept(initiatorID, targetID)
                cliques.cliques_make(initiatorID, targetID)
                # Get the new cliques AFTER this operation and
                # send the list relevant to every uer involved.
                newCliques = cliques.cliques_including(initiatorID, targetID)
                involvedUsers = set()
                for clique in newCliques:
                        involvedUsers.update(clique)
                for userID in involvedUsers:
                        if userID != targetID:
                                userCliques = cliques.cliques_get(userID)
                                notification = SHMessage()
                                notification.type = MessageType.CLIQUES_GET
                                notification.body = userCliques
                                send(notification, userID)

                # The target is the one who just accepted the request,
                # so return to them some info on the initiator who
                # added them.
                connection_data = models.User.get(userID=initiatorID)
                del connection_data[ProtocolKey.PASSWORD]
                del connection_data[ProtocolKey.SALT]
                del connection_data[ProtocolKey.REFERRER]
                response.body = connection_data
                # Notify the initiator if they're online.
                notification = SHMessage()
                notification.type = MessageType.CONNECTION_REQUEST_ACCEPTED
                target = models.User.get(userID=targetID)
                del target[ProtocolKey.PASSWORD]
                del target[ProtocolKey.SALT]
                del target[ProtocolKey.REFERRER]
                notification.body = target
                send(notification, initiatorID)

        return response


def request_decline(initiatorID, targetID):
        if initiatorID is None:
                raise ValueError("connectivity.request_decline(2): initiatorID argument is null")
        if targetID is None:
                raise ValueError("connectivity.request_decline(2): targetID argument is null")

        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUEST_DECLINE

        if initiatorID == targetID:
                response.errorCode = ConnectivityError.RECURSIVE
        else:
                models.UserConnection.remove(initiatorID, targetID)
                response.body[ProtocolKey.USER_ID] = initiatorID

                #TODO: NOTIFY THE INITIATOR IF THEY'RE ONLINE

        return response


def request_make(initiatorID, targetAlias):
        if initiatorID is None:
                raise ValueError("connectivity.request_make(2): initiatorID argument is null")
        if targetAlias is None:
                raise ValueError("connectivity.request_make(2): targetAlias argument is null")

        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUEST
        
        target = models.User.get(alias=targetAlias)
        if target is not None:
                targetID = target[ProtocolKey.USER_ID]
                if targetID == initiatorID:
                        response.errorCode = ConnectivityError.RECURSIVE
                else:
                        existing_connection = models.UserConnection.exists(initiatorID, targetID)
                        if existing_connection:
                                response.errorCode = ConnectivityError.EXISTS
                        else:
                                models.UserConnection.make(initiatorID, targetID)
                                # Notify the target if they're online.
                                #notification = SHMessage()
                                #notification.type = MessageType.CONNECTION_REQUESTED
                                #initiator = models.User.get(userID=initiatorID)
                                #notification.body[ProtocolKey.ALIAS] = initiator[ProtocolKey.ALIAS]
                                #notification.body[ProtocolKey.USER_ID] = initiator[ProtocolKey.USER_ID]
                                #send(notification, targetID)
                        
                        # Send back some useful info on the target.
                        response.body[ProtocolKey.ALIAS] = target[ProtocolKey.ALIAS]
                        response.body[ProtocolKey.USER_ID] = target[ProtocolKey.USER_ID]
        else:
                response.errorCode = ConnectivityError.NOT_FOUND
        
        return response


def request_revoke(initiatorID, targetID):
        if initiatorID is None:
                raise ValueError("connectivity.request_revoke(2): initiatorID argument is null")
        if targetID is None:
                raise ValueError("connectivity.request_revoke(2): targetID argument is null")

        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUEST_REVOKE

        if initiatorID == targetID:
                response.errorCode = ConnectivityError.RECURSIVE
        else:
                models.UserConnection.remove(initiatorID, targetID)
                response.body[ProtocolKey.USER_ID] = targetID

                # Notify the target if they're online.
                notification = SHMessage()
                notification.type = MessageType.CONNECTION_REQUEST_REVOKED
                notification.body[ProtocolKey.USER_ID] = initiatorID
                send(notification, targetID)

        return response


def requests_received_mark(userID, status):
        if userID is None:
                raise ValueError("connectivity.requests_received_mark(2): userID argument is null")
        elif status is None:
                raise ValueError("connectivity.requests_received_mark(2): status argument is null")

        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUESTS_MARK

        # Any non-zero value marks the requests as seen.
        if status != 0:
                status = 1

        models.UserConnection.mark(userID, status)

        return response


def requests_received_get(userID):
        if userID is None:
                raise ValueError("connectivity.requests_received_get(1): userID argument is null")

        requests = models.UserConnection.pending_requests_received_get(userID)
        # Rather than just returning the initiator's ID, 
        # return some other useful info to display.
        for request in requests:
                initiatorID = request[ProtocolKey.USER_ID]
                initiator = models.User.get(userID=initiatorID)
                request[ProtocolKey.ALIAS] = initiator[ProtocolKey.ALIAS]
                request[ProtocolKey.NAME] = initiator[ProtocolKey.NAME]
                
        return requests


def requests_sent_get(userID):
        if userID is None:
                raise ValueError("connectivity.requests_sent_get(1): userID argument is null")

        requests = models.UserConnection.pending_requests_sent_get(userID)
        # Rather than just returning the target's ID,
        # return some other useful info to display.
        for request in requests:
                targetID = request[ProtocolKey.USER_ID]
                target = models.User.get(userID=targetID)
                request[ProtocolKey.ALIAS] = target[ProtocolKey.ALIAS]
                request[ProtocolKey.NAME] = target[ProtocolKey.NAME]
        
        return requests
