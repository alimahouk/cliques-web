import uuid

from flask import request, session

from app import models
from app.constants import AdminError, CliqueError, ConnectivityError, ContentError, MessageType, PresenceError, ProtocolKey, SignupFormStatus
from controllers import admin, cliques, content, connectivity, identity, messaging, presence
from controllers.messaging import SHMessage, send


def clique_threads_get():
        response = SHMessage()
        response.type = MessageType.CLIQUE_THREADS_GET
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                cliqueID = request.form[ProtocolKey.CLIQUE_ID]
                response = content.clique_threads_get(userID, cliqueID)
        else:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()


def clique_thread_make():
        response = SHMessage()
        response.type = MessageType.CLIQUE_THREAD_MAKE
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                attachments = request.files.getlist(ProtocolKey.ATTACHMENTS + "[]")
                cliqueID = request.form[ProtocolKey.GROUP_ID]
                description = request.form[ProtocolKey.THREAD_DESCRIPTION]
                title = request.form[ProtocolKey.THREAD_TITLE]

                response = content.clique_thread_make(userID, cliqueID, title, description, attachments)
        else:
                response.errorCode = ContentError.BAD_REQUEST
        
        return response.serialise()


def clique_threads_mark_read():
        response = SHMessage()
        response.type = MessageType.CLIQUE_THREADS_MARK
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                threads = request.form[ProtocolKey.THREADS]
                status = int(request.form[ProtocolKey.THREAD_STATUS])
                
                threadList = [uuid.UUID(threadID) for threadID in threads.split(",")]
                response = content.clique_threads_mark(userID, threadList, status)
        else:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()


def cliques_get():
        response = SHMessage()
        response.type = MessageType.CLIQUES_GET

        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                response.body = cliques.cliques_get(userID)
        else:
                response.errorCode = CliqueError.BAD_REQUEST

        return response.serialise()


def comment_make():
        response = SHMessage()
        response.type = MessageType.COMMENT_MAKE
        if ProtocolKey.USER_ID in session:
                try:
                        userID = session[ProtocolKey.USER_ID]
                        attachments = request.files.getlist(ProtocolKey.ATTACHMENTS + "[]")
                        commentBody = request.form[ProtocolKey.COMMENT_BODY]
                        groupID = request.form[ProtocolKey.GROUP_ID]
                        postID = uuid.UUID(request.form[ProtocolKey.POST_ID])
                        threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])

                        response = content.comment_make(userID, postID, threadID, groupID, commentBody, attachments)
                except ValueError:
                        response.errorCode = ContentError.BAD_REQUEST
        else:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()


def comments_get():
        response = SHMessage()
        response.type = MessageType.COMMENTS_GET

        userID = None
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
        
        try:
                postID = uuid.UUID(request.form[ProtocolKey.POST_ID])

                if postID is not None:
                        groupID = None
                        if ProtocolKey.GROUP_ID in request.form:
                                groupID = request.form[ProtocolKey.GROUP_ID]

                        threadID = None
                        if ProtocolKey.POST_ID in request.form:
                                threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])

                        response = content.comments_get(userID, postID, threadID, groupID)
                else:
                        response.errorCode = ContentError.BAD_REQUEST
        except ValueError:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()


def connection_remove():
        response = SHMessage()
        response.type = MessageType.CONNECTION_REMOVE

        if ProtocolKey.USER_ID in session:
                if ProtocolKey.USER_ID in request.form:
                        userID = session[ProtocolKey.USER_ID]
                        # Everything coming via POST parameters is a string; we need ints.
                        targetID = int(request.form[ProtocolKey.USER_ID])
                        response = connectivity.connection_remove(userID, targetID)
                else:
                        response.errorCode = ConnectivityError.BAD_REQUEST
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def connection_request_accept():
        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUEST_ACCEPT

        if ProtocolKey.USER_ID in session:
                if ProtocolKey.USER_ID in request.form:
                        userID = session[ProtocolKey.USER_ID]
                        # Everything coming via POST parameters is a string; we need ints.
                        initiator = int(request.form[ProtocolKey.USER_ID])
                        response = connectivity.request_accept(initiator, userID)
                else:
                        response.errorCode = ConnectivityError.BAD_REQUEST
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def connection_request_decline():
        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUEST_DECLINE

        if ProtocolKey.USER_ID in session:
                if ProtocolKey.USER_ID in request.form:
                        userID = session[ProtocolKey.USER_ID]
                        # Everything coming via POST parameters is a string; we need ints.
                        initiator = int(request.form[ProtocolKey.USER_ID])
                        response = connectivity.request_decline(initiator, userID)
                else:
                        response.errorCode = ConnectivityError.BAD_REQUEST
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def connection_request_make():
        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUEST

        if ProtocolKey.USER_ID in session:
                if ProtocolKey.ALIAS in request.form:
                        userID = session[ProtocolKey.USER_ID]
                        target = request.form[ProtocolKey.ALIAS]
                        response = connectivity.request_make(userID, target)
                else:
                        response.errorCode = ConnectivityError.BAD_REQUEST
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def connection_request_revoke():
        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUEST_REVOKE

        if ProtocolKey.USER_ID in session:
                if ProtocolKey.USER_ID in request.form:
                        userID = session[ProtocolKey.USER_ID]
                        # Everything coming via POST parameters is a string; we need ints.
                        targetID = int(request.form[ProtocolKey.USER_ID])
                        response = connectivity.request_revoke(userID, targetID)
                else:
                        response.errorCode = ConnectivityError.BAD_REQUEST
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def connection_requests_received_get():
        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUESTS_RECEIVED_GET

        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                response.body = connectivity.requests_received_get(userID)
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def connection_requests_received_mark():
        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUESTS_MARK

        if ProtocolKey.USER_ID in session:
                status = int(request.form[ProtocolKey.STATUS])
                userID = session[ProtocolKey.USER_ID]
                response = connectivity.requests_received_mark(userID, status)
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def connection_requests_sent_get():
        response = SHMessage()
        response.type = MessageType.CONNECTION_REQUESTS_SENT_GET

        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                response.body = connectivity.requests_sent_get(userID)
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def connections_get():
        response = SHMessage()
        response.type = MessageType.CONNECTIONS_GET
        
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                response.body = connectivity.connections_get(userID)
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def invite_link_make():
        response = SHMessage()
        response.type = MessageType.INVITE_LINK_MAKE

        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                # This doesn't return a full link. It only creates a URL fragment.
                response = connectivity.invite_link_make(userID)
        else:
                response.errorCode = ConnectivityError.BAD_REQUEST

        return response.serialise()


def login():
        response = SHMessage()
        response.type = MessageType.LOG_IN

        alias = request.form[ProtocolKey.ALIAS]
        password = request.form[ProtocolKey.PASSWORD]

        response.errorCode = identity.login(alias, password)
        if response.errorCode == identity.LoginStatus.OK:
                userID = models.User.ID_get(alias)
                response.body[ProtocolKey.USER_ID] = userID
                session[ProtocolKey.USER_ID] = userID

        return response.serialise()


def lr_all_get():
        response = SHMessage()
        response.type = MessageType.LR_GET
        if ProtocolKey.USER_ID in session:
                homeRoomID = content.lr_room_id_get(request)

                if models.LivingRoom.get(homeRoomID) is None:
                        homeRoomID = None # Unsupported country.

                response.body[ProtocolKey.ROOMS] = content.lr_all_get()
                response.body[ProtocolKey.ROOM_HOME] = homeRoomID
        else:
                response.errorCode = ContentError.BAD_REQUEST
        
        return response.serialise()


def lr_thread_make():
        response = SHMessage()
        response.type = MessageType.LR_THREAD_MAKE
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                attachments = request.files.getlist(ProtocolKey.ATTACHMENTS + "[]")
                roomID = request.form[ProtocolKey.GROUP_ID]
                description = request.form[ProtocolKey.THREAD_DESCRIPTION]
                title = request.form[ProtocolKey.THREAD_TITLE]

                # A user can only make new threads in their homeroom.
                homeRoomID = content.lr_room_id_get(request)

                # homeRoomID == None means an unsupported country.
                if models.LivingRoom.get(homeRoomID) is None or roomID != homeRoomID:
                        response.errorCode = ContentError.FORBIDDEN
                else:
                        response = content.lr_thread_make(userID, roomID, title, description, attachments)
        else:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()


def lr_threads_get():
        response = SHMessage()
        response.type = MessageType.LR_THREADS_GET
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]

                if ProtocolKey.GROUP_ID in request.form:
                        roomID = request.form[ProtocolKey.GROUP_ID]
                else:
                        roomID = content.lr_room_id_get(request)
                        if models.LivingRoom.get(roomID) is None:
                                # Unsupported country; use the first country in the supported list.
                                allRooms = models.LivingRoom.all_get()
                                if len(allRooms) > 0:
                                        firstRoom = allRooms[0]
                                        roomID = firstRoom[ProtocolKey.ROOM_ID]

                if roomID is not None:
                        response = content.lr_threads_get(userID, roomID)
                else:
                        response.errorCode = ContentError.UNKNOWN_ORIGIN
        else:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()


def lr_threads_mark_read():
        response = SHMessage()
        response.type = MessageType.LR_THREADS_MARK
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                threads = request.form[ProtocolKey.THREADS]
                status = int(request.form[ProtocolKey.THREAD_STATUS])

                threadList = [uuid.UUID(threadID) for threadID in threads.split(",")]
                response = content.lr_threads_mark(userID, threadList, status)
        else:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()


def post_make():
        response = SHMessage()
        response.type = MessageType.POST_MAKE
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                attachments = request.files.getlist(ProtocolKey.ATTACHMENTS + "[]")
                groupID = request.form[ProtocolKey.GROUP_ID]
                postBody = request.form[ProtocolKey.POST_BODY]
                threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])

                response = content.post_make(userID, groupID, threadID, postBody, attachments)
        else:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()


def posts_get():
        response = SHMessage()
        response.type = MessageType.POSTS_GET

        userID = None
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]

        try:
                threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])

                if threadID is not None:
                        groupID = None
                        if ProtocolKey.GROUP_ID in request.form:
                                groupID = request.form[ProtocolKey.GROUP_ID]
                        
                        response = content.posts_get(userID, threadID, groupID)
                else:
                        response.errorCode = ContentError.BAD_REQUEST
        except ValueError:
                response.errorCode = ContentError.BAD_REQUEST
        

        return response.serialise()


def thread_get():
        response = SHMessage()
        response.type = MessageType.THREAD_GET

        userID = None
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]

        try:
                threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])
                response = content.thread_get(threadID, userID)
        except ValueError:
                response.errorCode = ContentError.BAD_REQUEST

        return response.serialise()