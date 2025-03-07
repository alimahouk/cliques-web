from datetime import datetime
from operator import itemgetter
import errno
import os
import re
import unicodedata

from app import APP_ROOT, models
from app.constants import CommentType, ContentError, GroupType, MessageType, PostType, TextDirection, ThreadStatus, ThreadType, ProtocolKey
from controllers import cliques, identity, presence
from controllers.crypto import sha256_bytes
from controllers.messaging import SHMessage, send


def attachments_delete(authorID, attachmentDescriptions):
        userFileDir = os.path.join(APP_ROOT, "static", "files", "user", authorID)
        for attachmentDescription in attachmentDescriptions:
                fileExtension = attachmentDescription[ProtocolKey.ATTACHMENT_TYPE]
                filename = attachmentDescription[ProtocolKey.CHECKSUM]
                path = os.path.join(userFileDir, filename+fileExtension)
                if os.path.exists(path):
                        os.remove(path)


def attachments_parse(attachments):
        attachmentDescriptions = []
        for attachment in attachments:
                attachmentDescription = dict()
                attachment.seek(0)
                contents = attachment.read()
                checksum = sha256_bytes(contents)
                filename, fileExtension = os.path.splitext(attachment.filename)

                attachmentDescription[ProtocolKey.ATTACHMENT_TYPE] = fileExtension
                attachmentDescription[ProtocolKey.CHECKSUM] = checksum

                attachmentDescriptions.append(attachmentDescription)
        return attachmentDescriptions


# attachments and attachmentDescriptions must be of the same length.
def attachments_save(authorID, attachments, attachmentDescriptions):
        if attachments is None or len(attachments) == 0:
                return

        userFileDir = os.path.join(APP_ROOT, "static", "files", "user", str(authorID))
        try:
                os.makedirs(userFileDir)
        except OSError as e:
                if e.errno != errno.EEXIST:
                        raise

        for i, attachment in enumerate(attachments):
                attachmentDescription = attachmentDescriptions[i]
                fileExtension = attachmentDescription[ProtocolKey.ATTACHMENT_TYPE]
                filename = attachmentDescription[ProtocolKey.CHECKSUM]
                path = os.path.join(userFileDir, filename+fileExtension)
                attachment.save(path)


def clique_thread_make(authorID, cliqueID, title, description, attachments):
        if authorID is None:
                raise ValueError("content.clique_thread_make(5): authorID argument is null")
        elif cliqueID is None:
                raise ValueError("content.clique_thread_make(5): cliqueID argument is null")

        response = SHMessage()
        response.type = MessageType.CLIQUE_THREAD_MAKE

        # First check if the author is actually a member of this clique.
        isMember = models.CliqueMembership.exists(authorID, cliqueID)
        if not isMember:
                response.errorCode = ContentError.FORBIDDEN
                return response
        
        if description is not None:
                description = description.strip()
        
        title = title.strip()

        if title is None or len(title) == 0 or len(title) > 140:
                response.errorCode = ContentError.INVALID_THREAD_TITLE
        elif len(description) > 10000:
                response.errorCode = ContentError.INVALID_THREAD_DESCRIPTION
        else:
                attachmentDescriptions = attachments_parse(attachments)
                threadType = ThreadType.PLAIN
                threadID = models.Thread.make(threadType, authorID, cliqueID, title, description, attachmentDescriptions)
                timestamp = datetime.now().astimezone().isoformat()

                attachments_save(authorID, attachments, attachmentDescriptions)

                response.body[ProtocolKey.ATTACHMENTS] = attachmentDescriptions
                response.body[ProtocolKey.GROUP_ID] = cliqueID
                response.body[ProtocolKey.THREAD_ID] = threadID
                response.body[ProtocolKey.CREATION_DATE] = timestamp
                
                members = models.CliqueMembership.all_get(cliqueID, raw=True)
                # Make a list of all members excluding the sender.
                recipients = [member for member in members if member != authorID]
                models.ThreadStatus.make(threadID, recipients)

                # Insert the thread status field.
                threadStatus = {
                        ProtocolKey.STATUS: ThreadStatus.SENT,
                        ProtocolKey.TIMESTAMP: timestamp,
                }
                for member in members:
                        if member != authorID:
                                notification = SHMessage()
                                notification.type = MessageType.CLIQUE_THREAD
                                notification.body[ProtocolKey.ATTACHMENTS] = attachmentDescriptions
                                notification.body[ProtocolKey.CREATION_DATE] = timestamp
                                notification.body[ProtocolKey.GROUP_ID] = cliqueID
                                notification.body[ProtocolKey.LAST_MODIFICATION_DATE] = timestamp
                                notification.body[ProtocolKey.THREAD_DESCRIPTION] = description
                                notification.body[ProtocolKey.THREAD_ID] = threadID
                                notification.body[ProtocolKey.THREAD_STATUS] = threadStatus
                                notification.body[ProtocolKey.THREAD_TYPE] = threadType
                                notification.body[ProtocolKey.THREAD_TITLE] = title
                                notification.body[ProtocolKey.USER_ID] = authorID
                                send(notification, member)
                                clique_threads_mark(member, [threadID], ThreadStatus.DELIVERED)
        return response

def clique_threads_get(userID, cliqueID):
        response = SHMessage()
        response.type = MessageType.CLIQUE_THREADS_GET

        # --
        # PERMISSIONS CHECK
        # --
        # First check if the user is actually a member of this clique.
        isMember = models.CliqueMembership.exists(userID, cliqueID)
        if not isMember:
                response.errorCode = ContentError.FORBIDDEN
                return response

        threads = list(models.Thread.all_get(userID, cliqueID))
        if threads is not None:
                # Mark undelivered threads by others as delivered to this user.
                mark = []
                for thread in threads:
                        # Don't return the ghost flag.
                        del(thread[ProtocolKey.GHOSTED])

                        if thread[ProtocolKey.THREAD_TYPE] == ThreadType.PLAIN:
                                authorID = thread[ProtocolKey.USER_ID]
                                threadID = thread[ProtocolKey.THREAD_ID]
                                if authorID != userID:
                                        if ProtocolKey.THREAD_STATUS in thread and thread[ProtocolKey.THREAD_STATUS] is not None:
                                                threadStatus = thread[ProtocolKey.THREAD_STATUS]
                                                status = threadStatus[ProtocolKey.STATUS]
                                                if status == ThreadStatus.SENT:
                                                        threadStatus[ProtocolKey.STATUS] = ThreadStatus.DELIVERED
                                                        mark.append(threadID)
                                        else:
                                                # This branch is executed in cases where a user joins a superclique
                                                # and has no thread status previously created on threads belonging
                                                # to the subclique they were not a part of. We create a fresh status
                                                # entry here and then mark the thread as delivered.
                                                models.ThreadStatus.make(threadID, [userID])
                                                threadStatus = models.ThreadStatus.get(threadID, userID)
                                                threadStatus[ProtocolKey.STATUS] = ThreadStatus.DELIVERED
                                                thread[ProtocolKey.THREAD_STATUS] = threadStatus
                                                mark.append(threadID)

                models.ThreadStatus.mark(userID, mark, delivered=True)

        # Get the latest connection updates of all members.
        # This will craft custom thread entries and as such ought be done
        # after plain threads are marked as delivered.
        members = models.CliqueMembership.all_get(cliqueID, raw=False)
        addedPairs = []
        for member in members:
                memberID = member[ProtocolKey.USER_ID]
                recentConnections = models.UserConnection.recents(memberID)
                # Cleanup required! Connections are undirected so we don't want duplicate entries.
                # i.e. X connected with Y - Y connected with X
                cleanedRecents = []
                for recent in recentConnections:
                        pair = {memberID, recent[ProtocolKey.USER_ID]}
                        if pair not in addedPairs:
                                addedPairs.append(pair)
                                cleanedRecents.append(recent)

                if cleanedRecents is not None and len(cleanedRecents) > 0:
                        latestConnection = cleanedRecents[0]
                        connectionsUpdate = dict()
                        connectionsUpdate[ProtocolKey.THREAD_DESCRIPTION] = cleanedRecents
                        connectionsUpdate[ProtocolKey.THREAD_TYPE] = ThreadType.CONNECTION_UPDATE
                        # Timestamp of this thread is that of the latest connection.
                        connectionsUpdate[ProtocolKey.CREATION_DATE] = latestConnection[ProtocolKey.TIMESTAMP]
                        connectionsUpdate[ProtocolKey.AUTHOR] = member
                        threads.append(connectionsUpdate)

        # Sort again after inserting connection updates.
        # Threads are sorted in descending order.
        threads = sorted(threads, key=itemgetter(ProtocolKey.CREATION_DATE), reverse=True) 

        response.body = threads
        return response


def clique_threads_mark(userID, threads, status):
        if userID is None:
                raise ValueError("content.clique_threads_mark(3): userID argument is null")

        response = SHMessage()
        response.type = MessageType.CLIQUE_THREADS_MARK

        if threads is None or len(threads) == 0:
                response.errorCode = ContentError.BAD_REQUEST
                return response

        # Marking threads expects a list of threads belonging to
        # the same group. A heterogeneous list is illegal.
        cliqueID = None
        for threadID in threads:
                thread = models.Thread.get(threadID)
                if cliqueID is None:
                        cliqueID = thread[ProtocolKey.GROUP_ID]
                else:
                        if thread[ProtocolKey.GROUP_ID] != cliqueID:
                                response.errorCode = ContentError.BAD_REQUEST
                                return response
        
        # First check if the user is actually a member of this clique.
        isMember = models.CliqueMembership.exists(userID, cliqueID)
        if not isMember:
                response.errorCode = ContentError.FORBIDDEN
                return response

        if status == ThreadStatus.DELIVERED:
                models.ThreadStatus.mark(userID, threads, delivered=True)
        elif status == ThreadStatus.SEEN:
                models.ThreadStatus.mark(userID, threads, seen=True)

        return response


def comment_make(authorID, postID, threadID, groupID, commentBody, attachments):
        if authorID is None:
                raise ValueError("content.comment_make(5): authorID argument is null")
        elif postID is None:
                raise ValueError("content.comment_make(5): postID argument is null")
        elif groupID is None:
                raise ValueError("content.comment_make(5): groupID argument is null")

        response = SHMessage()
        response.type = MessageType.COMMENT_MAKE

        # First check if the parent post actually exists.
        post = models.Post.get(postID)
        if post is None:
                response.errorCode = ContentError.NOT_FOUND
                return response

        if commentBody is not None:
                commentBody = commentBody.strip()

        if commentBody is None or len(commentBody) == 0 or len(commentBody) > 10000:
                response.errorCode = ContentError.INVALID_POST_BODY
        else:
                user = models.User.get(userID=authorID)

                attachmentDescriptions = attachments_parse(attachments)
                commentType = CommentType.PLAIN
                commentID = models.Comment.make(commentType, authorID, threadID, postID, commentBody, attachmentDescriptions)
                timestamp = datetime.now().astimezone().isoformat()

                attachments_save(authorID, attachments, attachmentDescriptions)

                response.body[ProtocolKey.ATTACHMENTS] = attachmentDescriptions
                response.body[ProtocolKey.COMMENT_ID] = commentID
                response.body[ProtocolKey.CREATION_DATE] = timestamp
                response.body[ProtocolKey.GROUP_ID] = groupID
                response.body[ProtocolKey.LAST_MODIFICATION_DATE] = timestamp
                response.body[ProtocolKey.POST_ID] = postID
                response.body[ProtocolKey.THREAD_ID] = threadID

                # Realtime Comments
                # --
                # This is only supported for cliques at the moment.
                groupType = group_type_get(groupID)
                if groupType == GroupType.CLIQUE:
                        members = models.CliqueMembership.all_get(groupID, raw=True)
                        for member in members:
                                if member != authorID:
                                        notification = SHMessage()
                                        notification.type = MessageType.COMMENT
                                        notification.body[ProtocolKey.ATTACHMENTS] = attachmentDescriptions
                                        notification.body[ProtocolKey.AUTHOR] = {
                                                ProtocolKey.USER_ID: authorID,
                                                ProtocolKey.ALIAS: user[ProtocolKey.ALIAS],
                                                ProtocolKey.NAME: user[ProtocolKey.NAME]
                                        }
                                        notification.body[ProtocolKey.COMMENT_BODY] = commentBody
                                        notification.body[ProtocolKey.COMMENT_ID] = commentID
                                        notification.body[ProtocolKey.COMMENT_TYPE] = commentType
                                        notification.body[ProtocolKey.CREATION_DATE] = timestamp
                                        notification.body[ProtocolKey.GROUP_ID] = groupID
                                        notification.body[ProtocolKey.LAST_MODIFICATION_DATE] = timestamp
                                        notification.body[ProtocolKey.POST_ID] = postID
                                        notification.body[ProtocolKey.THREAD_ID] = threadID
                                        send(notification, member)

        return response


def comments_get(userID, postID, threadID, groupID):
        response = SHMessage()
        response.type = MessageType.COMMENTS_GET

        # Background checks.
        post = models.Post.get(postID)
        if post is None:
                response.errorCode = ContentError.NOT_FOUND
                return response

        threadID = post[ProtocolKey.THREAD_ID]
        thread = models.Thread.get(threadID)

        if thread is None:
                response.errorCode = ContentError.NOT_FOUND
                return response
        
        groupID = thread[ProtocolKey.GROUP_ID]
        # Check what kind of group this thread belongs to.
        groupType = group_type_get(groupID)
        if groupType == GroupType.CLIQUE:
                if userID is None:
                        # Public viewer.
                        response.errorCode = ContentError.FORBIDDEN
                        return response
                # First check if the user is actually a member of this clique.
                isMember = models.CliqueMembership.exists(userID, groupID)
                if not isMember and not cliques.superclique_exists(userID, groupID):
                        response.errorCode = ContentError.FORBIDDEN
                        return response
        
        comments = list(models.Comment.all_get(postID))
        if comments is not None:
                for comment in comments:
                        authorID = comment[ProtocolKey.USER_ID]

                        comment[ProtocolKey.AUTHOR] = {
                                ProtocolKey.USER_ID: authorID,
                                ProtocolKey.ALIAS: comment[ProtocolKey.ALIAS],
                                ProtocolKey.NAME: comment[ProtocolKey.NAME]
                        }
                        # Delete the loose entries.
                        del(comment[ProtocolKey.ALIAS])
                        del(comment[ProtocolKey.NAME])
                        del(comment[ProtocolKey.USER_ID])

                        if groupID is not None:
                                comment[ProtocolKey.GROUP_ID] = groupID
                        if threadID is not None:
                                comment[ProtocolKey.THREAD_ID] = threadID

        response.body[ProtocolKey.POST_ID] = postID
        response.body[ProtocolKey.COMMENTS] = comments
        return response


def group_type_get(groupID):
        if groupID is None:
                raise ValueError("content.group_type_get(1): groupID argument is null")
        
        groupType = GroupType.UNDEFINED

        clique = models.Clique.get(groupID)
        if clique is not None:
                groupType = GroupType.CLIQUE
        else:
                room = models.LivingRoom.get(groupID)
                if room is not None:
                        groupType = GroupType.LR
        
        return groupType


def html_ampersands(text):
        return text.replace("&", "&amp;")


def html_angled_brackets(text):
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text


def html_newlines(text):
        return text.replace("\n", "<br>")


def html_quotes(text, quoteSyntax):
        patternQuote = re.compile(r"(?xm)^" + quoteSyntax + r".+\n")
        truncateLen = len(quoteSyntax)
        for quote in re.findall(patternQuote, text):
                truncated = quote[truncateLen:-1]
                truncated = truncated.strip()
                text = text.replace(quote, f"<blockquote>{truncated}</blockquote>")

        return text


# !INCOMPLETE
def html_unordered_lists(text):
        patternListItem = re.compile(r"(?xm)^•.+\n")
        for listItem in re.findall(patternListItem, text):
                truncated = listItem[1:-1]
                truncated = truncated.strip()
                text = text.replace(listItem, f"<li>{truncated}</li>")
                
        return text


def html_urls(text):
        # John Gruber's regex to find URLs in plain text.
        patternURL = re.compile(r'(?i)\b((?:(http|https|ftp|ftps|gopher)?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?]))')
        patternEmail = re.compile(r'''
                        (?xm)  # verbose identify URLs in text (and multiline)
                     (?=^.{11} # Mail header matcher
             (?<!Message-ID:|  # rule out Message-ID's as best possible
                 In-Reply-To)) # ...and also In-Reply-To
                        (.*?)( # must grab to email to allow prior lookbehind
            ([A-Za-z0-9-]+\.)? # maybe an initial part: DAVID.mertz@gnosis.cx
                 [A-Za-z0-9-]+ # definitely some local user: MERTZ@gnosis.cx
                             @ # ...needs an at sign in the middle
                  (\w+\.?){2,} # at least two domain groups, e.g. (gnosis.)(cx)
             (?=[\s\.,>)'"\]]) # assert: followed by white or clause ending
                             ) # end of match group
                               ''')
        URLPrefixes = ("http://", "https://", "ftp://", "ftps://", "gopher://")
        for url in re.findall(patternURL, text):
                href = url[0]
                if not href.startswith(URLPrefixes):
                        # We can only assume http.
                        href = "http://" + href
                text = text.replace(url[0], f'<a href="{href}">{url[0]}</a>')	
        for email in re.findall(patternEmail, text):
                text = text.replace(email[1], '<a href="mailto:%(email)s">%(email)s</a>' % {"email" : email[1]})

        return text


def is_valid_email(email):
        if re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is None:
                return False
        else:
                return True


def lr_all_get():
        return models.LivingRoom.all_get()


def lr_room_id_get(request):
        # TESTING IP ADDRESSES
        # --
        # • 83.110.250.231 (United Arab Emirates)
        # • 81.170.86.11 (United Kingdom)
        # • 72.229.28.185 (United States)
        userAddress = identity.ip_address(request)
        if userAddress == "127.0.0.1":
                userAddress = "81.170.86.11"
        countryCode = identity.iso_code(userAddress)
        if countryCode is not None:
                return countryCode.lower()
        else:
                return None


def lr_thread_make(authorID, roomID, title, description, attachments):
        if authorID is None:
                raise ValueError("content.lr_thread_make(5): authorID argument is null")
        elif roomID is None:
                raise ValueError("content.lr_thread_make(5): roomID argument is null")

        response = SHMessage()
        response.type = MessageType.LR_THREAD_MAKE

        if description is not None:
                description = description.strip()

        title = title.strip()

        if title is None or len(title) == 0 or len(title) > 140:
                response.errorCode = ContentError.INVALID_THREAD_TITLE
        elif len(description) > 10000:
                response.errorCode = ContentError.INVALID_THREAD_DESCRIPTION
        else:
                attachmentDescriptions = attachments_parse(attachments)
                threadType = ThreadType.PLAIN
                threadID = models.Thread.make(threadType, authorID, roomID, title, description, attachmentDescriptions)
                timestamp = datetime.now().astimezone().isoformat()

                attachments_save(authorID, attachments, attachmentDescriptions)

                response.body[ProtocolKey.ATTACHMENTS] = attachmentDescriptions
                response.body[ProtocolKey.CREATION_DATE] = timestamp
                response.body[ProtocolKey.GROUP_ID] = roomID
                response.body[ProtocolKey.LAST_MODIFICATION_DATE] = timestamp
                response.body[ProtocolKey.THREAD_ID] = threadID
        return response


def lr_threads_get(userID, roomID):
        response = SHMessage()
        response.type = MessageType.LR_THREADS_GET

        threads = list(models.Thread.all_get(userID, roomID, LR=True))
        if threads is not None:
                # Mark undelivered threads by others as delivered to this user.
                mark = []
                for thread in threads:
                        # Don't return the ghost flag.
                        del(thread[ProtocolKey.GHOSTED])

                        if thread[ProtocolKey.THREAD_TYPE] == ThreadType.PLAIN:
                                authorID = thread[ProtocolKey.USER_ID]
                                threadID = thread[ProtocolKey.THREAD_ID]

                                thread[ProtocolKey.AUTHOR] = {
                                        ProtocolKey.USER_ID: authorID,
                                        ProtocolKey.ALIAS: thread[ProtocolKey.ALIAS],
                                        ProtocolKey.NAME: thread[ProtocolKey.NAME]
                                }
                                # Delete the loose entries.
                                del(thread[ProtocolKey.ALIAS])
                                del(thread[ProtocolKey.NAME])
                                del(thread[ProtocolKey.USER_ID])

                                if userID is not None and authorID != userID:
                                        if ProtocolKey.THREAD_STATUS in thread and thread[ProtocolKey.THREAD_STATUS] is not None:
                                                threadStatus = thread[ProtocolKey.THREAD_STATUS]
                                                status = threadStatus[ProtocolKey.STATUS]
                                                if status == ThreadStatus.SENT:
                                                        threadStatus[ProtocolKey.STATUS] = ThreadStatus.DELIVERED
                                                        mark.append(threadID)
                if userID is not None:
                        models.ThreadStatus.mark(userID, mark, delivered=True)

        response.body[ProtocolKey.ROOM_ID] = roomID
        response.body[ProtocolKey.THREADS] = threads
        return response


def lr_threads_mark(userID, threads, status):
        if userID is None:
                raise ValueError("content.lr_threads_mark(3): userID argument is null")

        response = SHMessage()
        response.type = MessageType.LR_THREADS_MARK

        for thread in threads:
                models.ThreadStatus.make(thread, [userID])

        if status == ThreadStatus.DELIVERED:
                models.ThreadStatus.mark(userID, threads, delivered=True)
        elif status == ThreadStatus.SEEN:
                models.ThreadStatus.mark(userID, threads, seen=True)

        return response


def post_make(authorID, groupID, threadID, postBody, attachments):
        if authorID is None:
                raise ValueError("content.post_make(5): authorID argument is null")
        elif groupID is None:
                raise ValueError("content.post_make(5): groupID argument is null")
        elif threadID is None:
                raise ValueError("content.post_make(5): threadID argument is null")

        response = SHMessage()
        response.type = MessageType.POST_MAKE

        # First check if the parent thread actually exists and that it's not locked.
        thread = models.Thread.get(threadID)
        if thread is None or \
           thread[ProtocolKey.DELETED] == 1:
                response.errorCode = ContentError.NOT_FOUND
                return response
        elif thread[ProtocolKey.LOCKED] == 1:
                response.errorCode = ContentError.FORBIDDEN
                return response
        # --
        # PERMISSIONS CHECK
        # --
        groupID = thread[ProtocolKey.GROUP_ID]
        # Check what kind of group this thread belongs to.
        groupType = group_type_get(groupID)
        if groupType == GroupType.CLIQUE:
                if authorID is None:
                        # Public viewer.
                        response.errorCode = ContentError.FORBIDDEN
                        return response
                # First check if the user is actually a member of this clique (or a superclique).
                isMember = models.CliqueMembership.exists(authorID, groupID)
                if not isMember and not cliques.superclique_exists(authorID, groupID):
                        response.errorCode = ContentError.FORBIDDEN
                        return response

        if postBody is not None:
                postBody = postBody.strip()

        if postBody is None or len(postBody) == 0 or len(postBody) > 10000:
                response.errorCode = ContentError.INVALID_POST_BODY
        else:
                #user = models.User.get(userID=authorID)

                attachmentDescriptions = attachments_parse(attachments)
                postType = PostType.PLAIN
                postID = models.Post.make(postType, authorID, threadID, postBody, attachmentDescriptions)
                timestamp = datetime.now().astimezone().isoformat()

                attachments_save(authorID, attachments, attachmentDescriptions)

                response.body[ProtocolKey.ATTACHMENTS] = attachmentDescriptions
                response.body[ProtocolKey.CREATION_DATE] = timestamp
                response.body[ProtocolKey.GROUP_ID] = groupID
                response.body[ProtocolKey.LAST_MODIFICATION_DATE] = timestamp
                response.body[ProtocolKey.POST_ID] = postID
                response.body[ProtocolKey.THREAD_ID] = threadID

                # Realtime Replies
                # --
                # This is only supported for cliques at the moment.
                #groupType = group_type_get(groupID)
                #if groupType == GroupType.CLIQUE:
                #	members = models.CliqueMembership.all_get(groupID, raw=True)
                #	for memberID in members:
                #		if memberID != authorID:
                #			notification = SHMessage()
                #			notification.type = MessageType.POST
                #			notification.body[ProtocolKey.ATTACHMENTS] = attachmentDescriptions
                #			notification.body[ProtocolKey.AUTHOR] = {
                #				ProtocolKey.USER_ID: authorID,
                #				ProtocolKey.ALIAS: user[ProtocolKey.ALIAS],
                #				ProtocolKey.NAME: user[ProtocolKey.NAME]
                #			}
                #			notification.body[ProtocolKey.CREATION_DATE] = timestamp
                #			notification.body[ProtocolKey.GROUP_ID] = groupID
                #			notification.body[ProtocolKey.LAST_MODIFICATION_DATE] = timestamp
                #			notification.body[ProtocolKey.POST_BODY] = postBody
                #			notification.body[ProtocolKey.POST_ID] = postID
                #			notification.body[ProtocolKey.POST_TYPE] = postType
                #			notification.body[ProtocolKey.THREAD_ID] = threadID
                #			send(notification, memberID)
        return response


def posts_get(userID, threadID, groupID):
        response = SHMessage()
        response.type = MessageType.POSTS_GET

        # Background checks.
        thread = models.Thread.get(threadID)
        if thread is None:
                response.errorCode = ContentError.NOT_FOUND
                return response

        # --
        # PERMISSIONS CHECK
        # --
        groupID = thread[ProtocolKey.GROUP_ID]
        # Check what kind of group this thread belongs to.
        groupType = group_type_get(groupID)
        if groupType == GroupType.CLIQUE:
                if userID is None:
                        # Public viewer.
                        response.errorCode = ContentError.FORBIDDEN
                        return response
                # First check if the user is actually a member of this clique (or a superclique).
                isMember = models.CliqueMembership.exists(userID, groupID)
                if not isMember and not cliques.superclique_exists(userID, groupID):
                        response.errorCode = ContentError.FORBIDDEN
                        return response
        
        posts = list(models.Post.all_get(threadID))
        if posts is not None:
                for post in posts:
                        authorID = post[ProtocolKey.USER_ID]

                        post[ProtocolKey.AUTHOR] = {
                                ProtocolKey.USER_ID: authorID,
                                ProtocolKey.ALIAS: post[ProtocolKey.ALIAS],
                                ProtocolKey.NAME: post[ProtocolKey.NAME]
                        }
                        # Delete the loose entries.
                        del(post[ProtocolKey.ALIAS])
                        del(post[ProtocolKey.NAME])
                        del(post[ProtocolKey.USER_ID])

                        if groupID is not None:
                                post[ProtocolKey.GROUP_ID] = groupID

        response.body[ProtocolKey.THREAD_ID] = threadID
        response.body[ProtocolKey.POSTS] = posts
        return response


def text_direction(text):
        probability = len([None for ch in text if unicodedata.bidirectional(ch) in ("R", "AL")])/float(len(text))
        if probability > 0.5:
                return TextDirection.RTL
        else:
                return TextDirection.LTR


# TODO
def thread_delete(authorID, threadID):
        if threadID is None:
                raise ValueError("content.thread_delete(1): threadID argument is null")
        
        response = SHMessage()
        response.type = MessageType.CLIQUE_THREAD_DELETE

        attachmentDescriptions = models.PostAttachment.all_get(threadID)
        attachments_delete(authorID, attachmentDescriptions)
        #models.Thread.delete(threadID)

        return response


def thread_get(threadID, userID):
        response = SHMessage()
        response.type = MessageType.THREAD_GET

        thread = models.Thread.get(threadID)
        if thread is None:
                response.errorCode = ContentError.NOT_FOUND
                return response

        # --
        # PERMISSIONS CHECK
        # --
        groupID = thread[ProtocolKey.GROUP_ID]
        # Check what kind of group this thread belongs to.
        groupType = group_type_get(groupID)
        if groupType == GroupType.CLIQUE:
                if userID is None:
                        # Public viewer.
                        response.errorCode = ContentError.FORBIDDEN
                        return response
                # First check if the user is actually a member of this clique (or a superclique).
                isMember = models.CliqueMembership.exists(userID, groupID)
                if not isMember and not cliques.superclique_exists(userID, groupID):
                        response.errorCode = ContentError.FORBIDDEN
                        return response

        if thread is not None:
                # Don't return the ghost flag.
                del(thread[ProtocolKey.GHOSTED])

                posts = list(models.Post.all_get(threadID))
                if posts is not None:
                        for post in posts:
                                authorID = post[ProtocolKey.USER_ID]

                                post[ProtocolKey.AUTHOR] = {
                                        ProtocolKey.USER_ID: authorID,
                                        ProtocolKey.ALIAS: post[ProtocolKey.ALIAS],
                                        ProtocolKey.NAME: post[ProtocolKey.NAME]
                                }
                                # Delete the loose entries.
                                del(post[ProtocolKey.ALIAS])
                                del(post[ProtocolKey.NAME])
                                del(post[ProtocolKey.USER_ID])

                                post[ProtocolKey.GROUP_ID] = groupID
                        thread[ProtocolKey.POSTS] = posts
                
                if thread[ProtocolKey.THREAD_TYPE] == ThreadType.PLAIN:
                        authorID = thread[ProtocolKey.USER_ID]
                        threadID = thread[ProtocolKey.THREAD_ID]

                        thread[ProtocolKey.AUTHOR] = {
                                ProtocolKey.USER_ID: authorID,
                                ProtocolKey.ALIAS: thread[ProtocolKey.ALIAS],
                                ProtocolKey.NAME: thread[ProtocolKey.NAME]
                        }
                        # Delete the loose entries.
                        del(thread[ProtocolKey.ALIAS])
                        del(thread[ProtocolKey.NAME])
                        del(thread[ProtocolKey.USER_ID])

                        if userID is None:
                                # Public viewer.
                                if ProtocolKey.THREAD_STATUS in thread:
                                        del(thread[ProtocolKey.THREAD_STATUS])
                        elif authorID != userID:
                                # Mark undelivered thread by others as delivered to this user.
                                mark = []
                                if ProtocolKey.THREAD_STATUS in thread and thread[ProtocolKey.THREAD_STATUS] is not None:
                                        threadStatus = thread[ProtocolKey.THREAD_STATUS]
                                        status = threadStatus[ProtocolKey.STATUS]
                                        if status == ThreadStatus.SENT:
                                                threadStatus[ProtocolKey.STATUS] = ThreadStatus.DELIVERED
                                                mark.append(threadID)
                                models.ThreadStatus.mark(userID, mark, delivered=True)

        response.body = thread
        return response
