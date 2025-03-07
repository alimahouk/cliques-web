from enum import auto, Enum, IntEnum


class AdminError(IntEnum):
        OK = 0
        BAD_REQUEST = auto()
        BAD_UUID = auto()
        EXISTS = auto()
        INVALID_ALIAS = auto()
        INVALID_NAME = auto()
        INVALID_THREAD_DESCRIPTION = auto()
        INVALID_THREAD_TITLE = auto()
        NOT_FOUND = auto()

class CliqueError(IntEnum):
        OK = 0
        BAD_REQUEST = auto()
        NOT_FOUND = auto()


class CommentType(IntEnum):
        PLAIN = 0


class ConnectivityError(IntEnum):
        OK = 0
        BAD_REQUEST = auto()
        EXISTS = auto()
        NOT_FOUND = auto()
        RECURSIVE = auto()


class ContentError(IntEnum):
        OK = 0
        BAD_REQUEST = auto()
        FORBIDDEN = auto()
        INVALID_ATTACHMENT = auto()
        INVALID_POST_BODY = auto()
        INVALID_THREAD_DESCRIPTION = auto()
        INVALID_THREAD_TITLE = auto()
        NOT_FOUND = auto()
        REPETITIVE = auto()
        UNKNOWN_ORIGIN = auto()


class GroupType(IntEnum):
        UNDEFINED = 0
        CLIQUE = auto()
        LR = auto()


class LoginStatus(IntEnum):
        OK = 0
        ERR_CREDENTIALS = auto()
        ERR_INVALID_ALIAS = auto()
        ERR_INVALID_ID = auto()
        ERR_INVALID_PASSWORD = auto()
        ERR_NOTFOUND = auto()
        ERR_SUSPENDED = auto()


class MessageType(IntEnum):
        UNDEFINED = 0
        CHECK_IN = auto()
        CLIQUE_THREAD = auto()
        CLIQUE_THREAD_DELETE = auto()
        CLIQUE_THREAD_MAKE = auto()
        CLIQUE_THREADS_GET = auto()
        CLIQUE_THREADS_MARK = auto()
        CLIQUES_GET = auto()
        COMMENT = auto()
        COMMENT_DELETE = auto()
        COMMENT_MAKE = auto()
        COMMENTS_GET = auto()
        CONNECTION_REMOVE = auto()
        CONNECTION_REMOVED = auto()
        CONNECTION_REQUEST = auto()
        CONNECTION_REQUEST_ACCEPT = auto()
        CONNECTION_REQUEST_ACCEPTED = auto()
        CONNECTION_REQUEST_DECLINE = auto()
        CONNECTION_REQUEST_DECLINED = auto()
        CONNECTION_REQUEST_REVOKE = auto()
        CONNECTION_REQUEST_REVOKED = auto()
        CONNECTION_REQUESTED = auto()
        CONNECTION_REQUESTS_MARK = auto()
        CONNECTION_REQUESTS_RECEIVED_GET = auto()
        CONNECTION_REQUESTS_SENT_GET = auto()
        CONNECTIONS_GET = auto()
        INVITE_LINK = auto()
        INVITE_LINK_MAKE = auto()
        LOG_IN = auto()
        LOG_OUT = auto()
        LR_GET = auto()
        LR_THREAD = auto()
        LR_THREAD_DELETE = auto()
        LR_THREAD_MAKE = auto()
        LR_THREADS_GET = auto()
        LR_THREADS_MARK = auto()
        POST = auto()
        POST_DELETE = auto()
        POST_MAKE = auto()
        POSTS_GET = auto()
        THREAD_GET = auto()


class PostType(IntEnum):
        PLAIN = 0


class PresenceError(IntEnum):
        OK = 0
        BAD_REQUEST = auto()


class ProtocolKey(str, Enum):
        ADMIN = "admin"
        ALIAS = "alias"
        ATTACHMENT_TYPE = "attachmentType"
        ATTACHMENTS = "attachments"
        AUTHOR = "author"
        CHECKSUM = "checksum"
        CLIQUE_ID = "cliqueID"
        COMMENT_BODY = "commentBody"
        COMMENT_ID = "commentID"
        COMMENT_TYPE = "commentType"
        COMMENTS = "comments"
        CONNECTION_REQUESTS = "connectionRequests"
        CONNECTIONS = "connections"
        COUNTRY_ISO_CODE = "countryCode"
        CREATION_DATE = "created"
        DELETED = "deleted"
        EMAIL_ADDRESS = "email"
        ERR_CODE = "errorCode"
        FILE = "file"
        GHOSTED = "ghosted"
        GROUP_ID = "groupID"
        IP_ADDRESS = "IPAddress"
        LAST_MODIFICATION_DATE = "modified"
        LOCKED = "locked"
        MEMBERS = "members"
        MESSAGE_BODY = "messageBody"
        MESSAGE_TYPE = "messageType"
        NAME = "name"
        PARTICIPANT_COUNT = "participantCount"
        PASSWORD = "password"
        POST_BODY = "postBody"
        POST_COUNT = "postCount"
        POST_ID = "postID"
        POST_TYPE = "postType"
        POSTS = "posts"
        REFERRER = "referrer"
        ROOM_HOME = "homeRoom"
        ROOM_ID = "roomID"
        ROOMS = "rooms"
        SALT = "salt"
        SECRET = "secret"
        SESSION_ID = "sessionID"
        STATUS = "status"
        SUSPENDED = "suspended"
        TEXT_DIRECTION = "textDirection"
        THREAD_DESCRIPTION = "threadDescription"
        THREAD_DESCRIPTION_RAW = "threadDescriptionRaw"
        THREAD_ID = "threadID"
        THREAD_STATUS = "threadStatus"
        THREAD_TITLE = "threadTitle"
        THREAD_TITLE_RAW = "threadTitleRaw"
        THREAD_TYPE = "threadType"
        THREADS = "threads"
        TIMESTAMP = "timestamp"
        USER = "user"
        USER_ID = "userID"
        UUID = "UUID"


# This is for controlling visibility of the
# signup form on the index page. CLOSED
# will override the presence of an invite
# code.
class SignupFormStatus(IntEnum):
        OPEN = 0
        INVITE = auto()
        CLOSED = auto()


class SignupStatus(IntEnum):
        OK = 0
        ERR_BAN = auto()
        ERR_EXISTS = auto()
        ERR_INVALID_ALIAS = auto()
        ERR_INVALID_EMAIL = auto()
        ERR_INVALID_NAME = auto()
        ERR_INVALID_PASSWORD = auto()


class TextDirection(IntEnum):
        LTR = 0
        RTL = auto()


class ThreadStatus(IntEnum):
        SENT = 0
        DELIVERED = auto()
        SEEN = auto()


class ThreadType(IntEnum):
        PLAIN = 0
        CONNECTION_UPDATE = auto()
        STATUS_UPDATE = auto()


class UserConnectionStatus(IntEnum):
        UNDEFINED = 0
        REQUESTED = auto()
        ESTABLISHED = auto()
        BLOCKED = auto()


class UserError(IntEnum):
        OK = 0
        BAD_REQUEST = auto()
        ERR_INVALID_ALIAS = auto()
        ERR_INVALID_EMAIL = auto()
        ERR_INVALID_NAME = auto()
        ERR_INVALID_PASSWORD = auto()
        EXPIRED_LINK = auto()
        NOT_FOUND = auto()


class UserPresence(IntEnum):
        OFFLINE = 0
        ONLINE = auto()
