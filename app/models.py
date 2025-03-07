#
# All database calls are made from this file.
#

import itertools
import uuid
from datetime import datetime

import MySQLdb as mySQL
import MySQLdb.cursors

from app import config, constants


class DB:
        connection = None

        def connect(self):
                self.connection = mySQL.connect(
                    **config.DB_CONFIG,
                    cursorclass=MySQLdb.cursors.DictCursor,
                    binary_prefix=True
                )

        # query() accepts a single query and returns a single result set.
        def query(self, sql, arguments=None):
                try:
                        cursor = self.connection.cursor()
                        cursor.execute(sql, arguments)
                except (AttributeError, mySQL.OperationalError):
                        self.connect()
                        cursor = self.connection.cursor()
                        cursor.execute(sql, arguments)
                
                return cursor
        
        # update() only accepts a list of queries to allow for multiple updates
        # in a single commit. arguments is a list of lists (2D list), one list per query.
        def update(self, sql, arguments=None):
                if not isinstance(sql, list):
                        raise ValueError("DB.update(3): sql argument is not of type list")
                try:
                        cursor = self.connection.cursor()

                        for i, stmt in enumerate(sql):
                                cursor.execute(stmt, arguments[i])
                        self.connection.commit()
                except (AttributeError, mySQL.OperationalError):
                        self.connect()
                        cursor = self.connection.cursor()
                        for i, stmt in enumerate(sql):
                                cursor.execute(stmt, arguments[i])
                        self.connection.commit()
                
                return cursor


db = DB()


class Clique:
        # This will return a list of IDs, not a list of dicts.
        @staticmethod
        def all_get(userID, raw=False):
                if userID is None:
                        raise ValueError("Clique.all_get(2): userID argument is null")

                if raw:
                        cursor = db.query('''SELECT cliqueID FROM clique_membership
                                        WHERE memberID = %s AND active = 1
                                        ORDER BY activation_timestamp DESC
                                        ''', [userID])
                        result = cursor.fetchall()
                        return [row[constants.ProtocolKey.CLIQUE_ID] for row in result]
                else:
                        cursor = db.query('''SELECT clique.cliqueID, timestamp FROM clique
                                        INNER JOIN clique_membership
                                        ON clique.cliqueID = clique_membership.cliqueID AND clique_membership.memberID = %s AND clique_membership.active = 1
                                        ORDER BY clique_membership.activation_timestamp DESC
                                        ''', [userID])
                        return cursor.fetchall()

        @staticmethod
        def delete(cliqueID=None):
                if cliqueID is None:
                        raise ValueError("Clique.delete(1): cliqueID argument is null")

                queryList = ['''DELETE FROM clique
                                WHERE cliqueID = %s''']
                argList = [[cliqueID]]
                db.update(queryList, argList)

                CliqueMembership.delete(cliqueID=cliqueID)
                CliqueRelationship.delete(cliqueID)

        @staticmethod
        def get(cliqueID=None, alias=None, tree=False):
                if cliqueID is None and alias is None:
                        raise ValueError("Clique.get(2): both arguments are null")
                elif cliqueID is None and tree:
                        raise ValueError("Clique.get(2): fetching a full clique tree using an alias is not supported. Use its ID.")

                if alias is not None:
                        cursor = db.query('''SELECT * FROM clique
                                        WHERE alias = %s
                                        ''', [alias])
                        return cursor.fetchone()
                elif cliqueID is not None:
                        if tree:
                                cursor = db.query('''SELECT child as cliqueID FROM clique_relationship
                                                WHERE parent = %s
                                                ''', [cliqueID])
                                return cursor.fetchall()
                        else:
                                cursor = db.query('''SELECT * FROM clique
                                        WHERE cliqueID = %s
                                        ''', [cliqueID])
                                return cursor.fetchone()
        
        @staticmethod
        def ID_get(alias):
                if alias is None:
                        raise ValueError("Clique.ID_get(1): alias argument is null")

                cursor = db.query('''SELECT * FROM clique
                                WHERE alias = %s
                                ''', [alias])
                result = cursor.fetchone()
                if result is not None:
                        return result[constants.ProtocolKey.CLIQUE_ID]
                else:
                        return None
        
        @staticmethod
        def make(cliqueID, alias=None):
                if cliqueID is None:
                        raise ValueError("Clique.make(2): cliqueID argument is null")

                queryList = ['''INSERT IGNORE INTO clique
                        (cliqueID, alias)
                        VALUES (%s, %s)''']
                argList = [[cliqueID, alias]]
                db.update(queryList, argList)


class CliqueMembership:
        @staticmethod
        def delete(cliqueID=None, userID=None):
                queryList = []
                argList = []
                if cliqueID is not None:
                        queryList.append('''INSERT IGNORE INTO clique
                                        (cliqueID, alias)
                                        VALUES (%s, %s)''')
                        argList.append([cliqueID])
                elif userID is not None:
                        queryList.append('''DELETE FROM clique_membership
                                        WHERE memberID = %s''')
                        argList.append([userID])
                db.update(queryList, argList)

        @staticmethod
        def activate(cliqueID, active=True, members=None):
                if cliqueID is None:
                        raise ValueError("CliqueMembership.activate(3): cliqueID argument is null")
                
                if members is not None and type(members) not in [list, tuple]:
                        raise ValueError("CliqueMembership.activate(3): members argument is not a list/tuple")

                queryList = []
                argList = []

                # The 'active' column only holds ints but this
                # function can also accept boolean types,
                # so we have to ensure we insert an int.
                if not active:
                        active = 0
                else:
                        active = 1

                if members is not None:
                        memberIDStr = ",".join(str(i) for i in members)
                        queryList.append('''UPDATE clique_membership
                                        SET active = %s, activation_timestamp = CURRENT_TIMESTAMP
                                        WHERE cliqueID = %s AND memberID IN (%s)''')
                        argList.append([active, cliqueID, memberIDStr])
                else:
                        queryList.append('''UPDATE clique_membership
                                        SET active = %s, activation_timestamp = CURRENT_TIMESTAMP
                                        WHERE cliqueID = %s''')
                        argList.append([active, cliqueID])
                db.update(queryList, argList)

        @staticmethod
        def all_get(cliqueID, activeOnly=True, raw=False):
                if cliqueID is None:
                        raise ValueError("CliqueMembership.all_get(1): cliqueID argument is null")

                if activeOnly:
                        activeOnly = 1
                else:
                        activeOnly = 0
                
                if raw:
                        # This will return a list of IDs, not a list of dicts.
                        cursor = db.query('''SELECT memberID as userID FROM clique_membership 
                                        WHERE cliqueID = %s AND active = %s
                                        ORDER BY memberID ASC
                                        ''', [cliqueID, activeOnly])
                        result = cursor.fetchall()
                        return [row[constants.ProtocolKey.USER_ID] for row in result]
                else:
                        cursor = db.query('''SELECT userID, alias FROM user
                                        INNER JOIN clique_membership
                                        ON clique_membership.cliqueID = %s AND clique_membership.active = %s AND clique_membership.memberID = user.userID
                                        ORDER BY alias
                                        ''', [cliqueID, activeOnly])
                        return cursor.fetchall()
        
        @staticmethod
        def exists(userID, cliqueID):
                if userID is None:
                        raise ValueError("CliqueMembership.exists(2): userID argument is null")
                elif cliqueID is None:
                        raise ValueError("CliqueMembership.exists(2): cliqueID argument is null")
                
                cursor = db.query('''SELECT * FROM clique_membership 
                                WHERE cliqueID = %s AND memberID = %s
                                ''', [cliqueID, userID])
                result = cursor.fetchone()
                if result is None:
                        return False
                else:
                        return True

        @staticmethod
        def make(cliqueID, members, active=True):
                if cliqueID is None:
                        raise ValueError("CliqueMembership.make(2): cliqueID argument is null")
                elif members is None:
                        raise ValueError("CliqueMembership.make(2): members argument is null")
                elif type(members) not in[list, tuple]:
                        raise ValueError("CliqueMembership.make(2): members argument is not a list/tuple")
                
                queryList = []
                argList = []

                if active:
                        active = 1
                else:
                        active = 0
                for memberID in members:
                        queryList.append('''INSERT IGNORE INTO clique_membership
                                        (cliqueID, memberID, active)
                                        VALUES (%s, %s, %s)''')
                        argList.append([cliqueID, memberID, active])
                db.update(queryList, argList)

                # Prepare for the next update.
                queryList.clear()
                argList.clear()

                # Existing memberships won't be overwritten, so just activate them.
                queryList.append('''UPDATE clique_membership
                                SET active = %s
                                WHERE cliqueID = %s AND memberID IN (''' + ", ".join(str(memberID) for memberID in members) + ")")
                argList.append([active, cliqueID])
                db.update(queryList, argList)


class CliqueRelationship:
        @staticmethod
        def delete(cliqueID):
                if cliqueID is None:
                        raise ValueError("CliqueRelationship.delete(1): cliqueID argument is null")

                queryList = ['''DELETE FROM clique_relationship
                                WHERE parent = %s OR child = %s''']
                argList = [[cliqueID, cliqueID]]
                db.update(queryList, argList)

        @staticmethod
        def make(parent, children):
                if parent is None:
                        raise ValueError("CliqueRelationship.make(2): parent argument is null")
                
                queryList = []
                argList = []
                
                if children is not None and len(children) > 0:
                        for child in children:
                                queryList.append('''INSERT IGNORE INTO clique_relationship
                                                (parent, child)
                                                VALUES (%s, %s)''')
                                argList.append([parent, child])
                        db.update(queryList, argList)


class Comment:
        @staticmethod
        def all_get(postID, limit=100):
                if postID is None:
                        raise ValueError("Comment.all_get(2): postID argument is null")
                
                cursor = db.query('''SELECT comment.*, user.alias, user.name FROM comment
                                LEFT JOIN user ON comment.userID = user.userID
                                WHERE comment.postID = %s
                                ORDER BY created ASC
                                LIMIT %s
                                ''', [postID.bytes, limit])
                comments = cursor.fetchall()
                # Convert the IDs from binary to UUIDs.
                for comment in comments:
                        commentID = uuid.UUID(bytes=comment[constants.ProtocolKey.COMMENT_ID])
                        postID = uuid.UUID(bytes=comment[constants.ProtocolKey.POST_ID])
                        threadID = uuid.UUID(bytes=comment[constants.ProtocolKey.THREAD_ID])

                        comment[constants.ProtocolKey.COMMENT_ID] = commentID
                        comment[constants.ProtocolKey.POST_ID] = postID
                        comment[constants.ProtocolKey.THREAD_ID] = threadID

                return comments

        @staticmethod
        def count():
                cursor = db.query('''SELECT * FROM comment''', None)
                return len(cursor.fetchall()) 

        # Pass a postID to delete all comments belonging to it.
        #
        # Caution: this method actually erases the records. It does not simply
        # mark the comment as deleted.
        @staticmethod
        def erase(commentID=None, postID=None):
                queryList = []
                argList = []

                if postID is not None:
                        queryList.append('''DELETE FROM comment
                                        WHERE postID = %s''')
                        argList.append([postID.bytes])
                elif commentID is not None:
                        queryList.append('''DELETE FROM comment
                                        WHERE commentID = %s''')
                        argList.append([commentID.bytes])

                db.update(queryList, argList)

        @staticmethod
        def get(commentID):
                if commentID is None:
                        raise ValueError("Comment.get(1): commentID argument is null")
                
                cursor = db.query('''SELECT comment.*, user.alias, user.name FROM comment
                                LEFT JOIN user ON comment.userID = user.userID
                                WHERE comment.commentID = %s
                                ''', [commentID.bytes])
                comment = cursor.fetchone()
                if comment is not None:
                        commentID = uuid.UUID(bytes=comment[constants.ProtocolKey.COMMENT_ID])
                        postID = uuid.UUID(bytes=comment[constants.ProtocolKey.POST_ID])
                        threadID = uuid.UUID(bytes=comment[constants.ProtocolKey.THREAD_ID])

                        comment[constants.ProtocolKey.COMMENT_ID] = commentID
                        comment[constants.ProtocolKey.POST_ID] = postID
                        comment[constants.ProtocolKey.THREAD_ID] = threadID

                return comment

        @staticmethod
        def make(commentType, authorID, threadID, postID, commentBody, attachmentDescriptions):
                if authorID is None:
                        raise ValueError("Comment.make(6): authorID argument is null")
                elif threadID is None:
                        raise ValueError("Comment.make(6): threadID argument is null")
                elif postID is None:
                        raise ValueError("Comment.make(6): postID argument is null")

                commentID = uuid.uuid4()
                queryList = ['''INSERT INTO comment
                                (commentID, commentType, threadID, postID, userID, commentBody)
                                VALUES (%s, %s, %s, %s, %s, %s)''']
                argList = [[commentID.bytes, commentType.value, threadID.bytes, postID.bytes, authorID, commentBody]]
                db.update(queryList, argList)

                #CommentAttachment.make(commentID, attachmentDescriptions)
                
                return commentID


class InviteCode:
        @staticmethod
        def all_delete(userID):
                queryList = ['''DELETE FROM invite_code
                                WHERE userID = %s''']
                argList = [[userID]]
                db.update(queryList, argList)

        @staticmethod
        def delete(code):
                queryList = ['''DELETE FROM invite_code
                                WHERE code = %s''']
                argList = [[code]]
                db.update(queryList, argList)
        
        @staticmethod
        def get(userID=None, code=None):
                if userID is None and code is None:
                        raise ValueError("InviteCode.get(2): both arguments are null")
                
                if code is not None:
                        cursor = db.query('''SELECT * FROM invite_code
                                        WHERE code = %s
                                        ''', [code])
                        return cursor.fetchone()
                else:
                        cursor = db.query('''SELECT * FROM invite_code
                                        WHERE userID = %s
                                        ''', [userID])
                        return cursor.fetchall()

        # userID is the user making the request.
        @staticmethod
        def make(userID, code):
                if userID is None:
                        raise ValueError("InviteCode.make(2): userID argument is null")
                if code is None:
                        raise ValueError("InviteCode.make(2): code argument is null")
                
                queryList = ['''INSERT INTO invite_code
                                (userID, code)
                                VALUES (%s, %s)''']
                argList = [[userID, code]]
                db.update(queryList, argList)


class LivingRoom:
        @staticmethod
        def all_get():
                cursor = db.query('''SELECT * FROM living_room
                                ORDER BY name ASC
                                ''', None)
                return cursor.fetchall()
        
        @staticmethod
        def get(roomID):
                if roomID is None:
                        return None

                cursor = db.query('''SELECT * FROM living_room
                                WHERE roomID = %s
                                ''', [roomID])
                return cursor.fetchone()


class Post:
        # Pass limit = 0 to get ALL posts. 
        @staticmethod
        def all_get(threadID, limit=100):
                if threadID is None:
                        raise ValueError("Post.all_get(2): threadID argument is null")
                
                if limit == 0:
                        cursor = db.query('''SELECT post.*, user.alias, user.name FROM post
                                        LEFT JOIN user ON post.userID = user.userID
                                        WHERE post.threadID = %s
                                        ORDER BY created DESC
                                        ''', [threadID.bytes])
                else:
                        cursor = db.query('''SELECT post.*, user.alias, user.name FROM post
                                        LEFT JOIN user ON post.userID = user.userID
                                        WHERE post.threadID = %s
                                        ORDER BY created DESC
                                        LIMIT %s
                                        ''', [threadID.bytes, limit])
                posts = cursor.fetchall()
                # Convert the IDs from binary to UUIDs.
                for post in posts:
                        postID = uuid.UUID(bytes=post[constants.ProtocolKey.POST_ID])
                        post[constants.ProtocolKey.POST_ID] = postID
                        threadID = uuid.UUID(bytes=post[constants.ProtocolKey.THREAD_ID])
                        post[constants.ProtocolKey.THREAD_ID] = threadID

                return posts
        
        @staticmethod
        def count():
                cursor = db.query('''SELECT * FROM post''', None)
                return len(cursor.fetchall()) 

        # Pass a threadID to delete all posts belonging to it.
        #
        # Caution: this method actually erases the records. It does not simply
        # mark the post as deleted.
        @staticmethod
        def erase(postID=None, threadID=None):
                queryList = []
                argList = []

                if threadID is not None:
                        queryList.append('''DELETE FROM post
                                        WHERE threadID = %s''')
                        argList.append([threadID.bytes])
                elif postID is not None:
                        queryList.append('''DELETE FROM post
                                        WHERE postID = %s''')
                        argList.append([postID.bytes])

                db.update(queryList, argList)


        @staticmethod
        def get(postID):
                if postID is None:
                        raise ValueError("Post.get(1): postID argument is null")
                
                cursor = db.query('''SELECT post.*, user.alias, user.name FROM post
                                LEFT JOIN user ON post.userID = user.userID
                                WHERE post.postID = %s
                                ''', [postID.bytes])
                post = cursor.fetchone()
                if post is not None:
                        postID = uuid.UUID(bytes=post[constants.ProtocolKey.POST_ID])
                        post[constants.ProtocolKey.POST_ID] = postID
                        threadID = uuid.UUID(bytes=post[constants.ProtocolKey.THREAD_ID])
                        post[constants.ProtocolKey.THREAD_ID] = threadID

                return post

        @staticmethod
        def make(postType, authorID, threadID, postBody, attachmentDescriptions):
                if authorID is None:
                        raise ValueError("Post.make(5): authorID argument is null")
                elif threadID is None:
                        raise ValueError("Post.make(5): threadID argument is null")

                postID = uuid.uuid4()
                queryList = ['''INSERT INTO post
                                (postID, postType, threadID, userID, postBody)
                                VALUES (%s, %s, %s, %s, %s)''']
                argList = [[postID.bytes, postType.value, threadID.bytes, authorID, postBody]]
                db.update(queryList, argList)

                #PostAttachment.make(postID, attachmentDescriptions)
                
                return postID


class PostAttachment:
        @staticmethod
        def all_get(postID):
                if postID is None:
                        raise ValueError("PostAttachment.all_get(1): postID argument is null")

                cursor = db.query('''SELECT * FROM post_attachment
                                WHERE postID = %s
                                ''', [postID.bytes])
                attachments = cursor.fetchall()
                # Convert the ID from binary to UUIDs.
                for attachment in attachments:
                        postID = uuid.UUID(bytes=attachment[constants.ProtocolKey.POST_ID])
                        attachment[constants.ProtocolKey.POST_ID] = postID

                return attachments

        @staticmethod
        def delete(postID=None, attachmentID=None):
                queryList = []
                argList = []

                if postID is not None:
                        queryList.append('''DELETE FROM post_attachment
                                        WHERE postID = %s''')
                        argList.append([postID.bytes])
                elif attachmentID is not None:
                        queryList.append('''DELETE FROM post_attachment
                                        WHERE attachmentID = %s''')
                        argList.append([attachmentID.bytes])
                db.update(queryList, argList)

        @staticmethod
        def make(postID, attachmentDescriptions):
                if postID is None:
                        raise ValueError("PostAttachment.make(2): postID argument is null")
                
                if attachmentDescriptions is None or len(attachmentDescriptions) == 0:
                        return

                # TODO Fix up this function to generate UUIDs for each attachment before insertion.
                return

                query = '''INSERT INTO post_attachment
                        (attachmentID, attachmentType, postID, checksum)
                        VALUES ''' + ", ".join(f"('{description[constants.ProtocolKey.ATTACHMENT_TYPE]}', {description[constants.ProtocolKey.POST_ID]}, '{description[constants.ProtocolKey.CHECKSUM]}')" for description in attachmentDescriptions)
                db.update(query, None)


class Thread:
        # userID is the user making the request.
        @staticmethod
        def all_get(userID, groupID, limit=100, LR=False):
                if groupID is None:
                        raise ValueError("Thread.all_get(4): groupID argument is null")
                
                if LR:
                        # Threads fetched for a living room are treated slightly differently.
                        if userID is not None:
                                query = '''SELECT thread.*, user.alias, user.name FROM thread
                                        LEFT JOIN user ON thread.userID = user.userID
                                        WHERE thread.groupID = %s AND thread.deleted = 0 AND (thread.ghosted = 0 OR (thread.ghosted = 1 AND thread.userID = %s))
                                        ORDER BY created DESC
                                        LIMIT %s
                                        '''
                                args = [groupID, userID, limit]
                        else:
                                query = '''SELECT thread.*, user.alias, user.name FROM thread
                                        LEFT JOIN user ON thread.userID = user.userID
                                        WHERE thread.groupID = %s AND thread.deleted = 0 AND thread.ghosted = 0
                                        ORDER BY created DESC
                                        LIMIT %s
                                        '''
                                args = [groupID, limit]
                else:
                        query = '''SELECT * FROM thread
                                WHERE groupID = %s OR groupID IN
                                (SELECT child FROM clique_relationship
                                WHERE clique_relationship.parent = %s)
                                ORDER BY created DESC
                                LIMIT %s
                                '''
                        args = [groupID, groupID, limit]

                cursor = db.query(query, args)
                threads = cursor.fetchall()

                for thread in threads:
                        # Convert the ID bytes back into a UUID.
                        threadID = uuid.UUID(bytes=thread[constants.ProtocolKey.THREAD_ID])

                        author = thread[constants.ProtocolKey.USER_ID]
                        postParticipantCount = Thread.count_post_participants(threadID)
                        postCount = Thread.count_posts(threadID)

                        thread[constants.ProtocolKey.PARTICIPANT_COUNT] = postParticipantCount
                        thread[constants.ProtocolKey.POST_COUNT] = postCount
                        thread[constants.ProtocolKey.THREAD_ID] = threadID

                        if LR:
                                if userID:
                                        # Get the user's status on threads made by others.
                                        thread[constants.ProtocolKey.THREAD_STATUS] = ThreadStatus.get(threadID, userID)
                                        if thread[constants.ProtocolKey.THREAD_STATUS] is None:
                                                thread[constants.ProtocolKey.THREAD_STATUS] = {constants.ProtocolKey.STATUS: constants.ThreadStatus.SENT}
                        else:
                                if userID is not None and author == userID:
                                        # Get the status of threads belonging to the user who made the request.
                                        thread[constants.ProtocolKey.THREAD_STATUS] = ThreadStatus.all_get(threadID)
                                else:
                                        # Get the user's status on threads made by others.
                                        thread[constants.ProtocolKey.THREAD_STATUS] = ThreadStatus.get(threadID, userID)
                

                return threads
        
        @staticmethod
        def count():
                cursor = db.query('''SELECT * FROM thread''', None)
                return len(cursor.fetchall())
        
        @staticmethod
        def count_post_participants(threadID):
                if threadID is None:
                        raise ValueError("Thread.count_post_participants(1): threadID argument is null")

                cursor = db.query('''SELECT COUNT(DISTINCT userID) as participantCount FROM post
                                WHERE threadID = %s
                                ''', [threadID.bytes])
                result = cursor.fetchone()
                return result["participantCount"]

        @staticmethod
        def count_posts(threadID):
                if threadID is None:
                        raise ValueError("Thread.count_posts(1): threadID argument is null")

                cursor = db.query('''SELECT * FROM post
                                WHERE threadID = %s
                                ''', [threadID.bytes])
                return len(cursor.fetchall())
        
        # Caution: this method actually erases the record. It does not simply
        # mark the thread as deleted.
        @staticmethod
        def erase(threadID):
                if threadID is None:
                        raise ValueError("Thread.erase(1): threadID argument is null")
                
                queryList = ['''DELETE FROM thread
                                WHERE threadID = %s''']
                argList = [[threadID.bytes]]
                db.update(queryList, argList)

                ThreadStatus.delete(threadID=threadID)
                PostAttachment.delete(postID=threadID)

        @staticmethod
        def get(threadID):
                if threadID is None:
                        raise ValueError("Thread.get(1): threadID argument is null")
                
                cursor = db.query('''SELECT thread.*, user.alias, user.name FROM thread
                                LEFT JOIN user ON thread.userID = user.userID
                                WHERE thread.threadID = %s
                                ''', [threadID.bytes])
                thread = cursor.fetchone()
                if thread is not None:
                        # Convert the ID bytes back into a UUID.
                        threadID = uuid.UUID(bytes=thread[constants.ProtocolKey.THREAD_ID])
                        postParticipantCount = Thread.count_post_participants(threadID)
                        postCount = Thread.count_posts(threadID)

                        thread[constants.ProtocolKey.PARTICIPANT_COUNT] = postParticipantCount
                        thread[constants.ProtocolKey.POST_COUNT] = postCount
                        thread[constants.ProtocolKey.THREAD_ID] = threadID

                return thread

        @staticmethod
        def ghost(threadID, ghost):
                if threadID is None:
                        raise ValueError("Thread.ghost(2): threadID argument is null")
                elif ghost is None:
                        raise ValueError("Thread.ghost(2): ghost argument is null")
                
                queryList = ['''UPDATE thread
                                SET ghosted = %s
                                WHERE threadID = %s''']
                argList = [[ghost, threadID.bytes]]
                db.update(queryList, argList)

        @staticmethod
        def lock(threadID, lock):
                if threadID is None:
                        raise ValueError("Thread.lock(2): threadID argument is null")
                elif lock is None:
                        raise ValueError("Thread.lock(2): lock argument is null")
                
                queryList = ['''UPDATE thread
                                SET locked = %s
                                WHERE threadID = %s''']
                argList = [[lock, threadID.bytes]]
                db.update(queryList, argList)

        @staticmethod
        def make(threadType, authorID, groupID, title, description, attachmentDescriptions):
                if authorID is None:
                        raise ValueError("Thread.make(6): authorID argument is null")
                elif groupID is None:
                        raise ValueError("Thread.make(6): groupID argument is null")

                threadID = uuid.uuid4()
                queryList = ['''INSERT INTO thread
                                (threadID, threadType, groupID, userID, threadTitle, threadDescription)
                                VALUES (%s, %s, %s, %s, %s, %s)''']
                argList = [[threadID.bytes, threadType.value, groupID, authorID, title, description]]
                db.update(queryList, argList)

                #PostAttachment.make(threadID, attachmentDescriptions)
                
                return threadID
        
        @staticmethod
        def modify(threadID, title, description):
                if threadID is None:
                        raise ValueError("Thread.modify(3): threadID argument is null")
                elif title is None:
                        raise ValueError("Thread.modify(3): title argument is null")
                
                queryList = ['''UPDATE thread
                                SET threadTitle = %s, threadDescription = %s, modified = CURRENT_TIMESTAMP
                                WHERE threadID = %s''']
                argList = [[title, description, threadID.bytes]]
                db.update(queryList, argList)

                
class ThreadStatus:
        @staticmethod
        def all_get(threadID):
                if threadID is None:
                        raise ValueError("ThreadStatus.all_get(1): threadID argument is null")
                
                cursor = db.query('''SELECT * FROM thread_status
                                WHERE threadID = %s
                                ''', [threadID.bytes])
                statuses = cursor.fetchall()
                # Convert the threadIDs from binary to UUIDs.
                for status in statuses:
                        threadID = uuid.UUID(bytes=status[constants.ProtocolKey.THREAD_ID])
                        status[constants.ProtocolKey.THREAD_ID] = threadID

                return statuses

        @staticmethod
        def delete(threadID=None, userID=None):
                queryList = []
                argList = []

                if threadID is not None:
                        queryList.append('''DELETE FROM thread_status
                                        WHERE threadID = %s''')
                        argList.append([threadID.bytes])
                elif userID is not None:
                        queryList.append('''DELETE FROM thread_status
                                        WHERE userID = %s''')
                        argList.append([userID])
                db.update(queryList, argList)

        @staticmethod
        def get(threadID, userID):
                if threadID is None:
                        raise ValueError("ThreadStatus.get(2): threadID argument is null")
                elif userID is None:
                        raise ValueError("ThreadStatus.get(2): userID argument is null")

                cursor = db.query('''SELECT * FROM thread_status
                                WHERE threadID = %s AND userID = %s
                                ''', [threadID.bytes, userID])
                # Convert the threadID from binary to a UUID.
                status = cursor.fetchone()
                if status is not None:
                        threadID = uuid.UUID(bytes=status[constants.ProtocolKey.THREAD_ID])
                        status[constants.ProtocolKey.THREAD_ID] = threadID

                return status

        @staticmethod
        def make(threadID, users):
                if threadID is None:
                        raise ValueError("ThreadStatus.make(2): threadID argument is null")
                elif users is None:
                        raise ValueError("ThreadStatus.make(2): users argument is null")

                queryList = []
                argList = []

                for userID in users:
                        queryList.append('''INSERT IGNORE INTO thread_status
                                        (threadID, userID)
                                        VALUES (%s, %s)''')
                        argList.append([threadID.bytes, userID])
                db.update(queryList, argList)

        @staticmethod
        def mark(userID, threads, delivered=False, seen=False):
                if userID is None:
                        raise ValueError("ThreadStatus.mark(4): userID argument is null")
                elif threads is None:
                        raise ValueError("ThreadStatus.mark(4): threads argument is null")

                if len(threads) == 0:
                        return

                queryList = []
                argList = []

                if seen:
                        status = constants.ThreadStatus.SEEN.value
                elif delivered:
                        status = constants.ThreadStatus.DELIVERED.value
                else:
                        status = constants.ThreadStatus.SENT.value
                
                for threadID in threads:
                        queryList.append('''UPDATE thread_status
                                        SET status = %s, timestamp = CURRENT_TIMESTAMP
                                        WHERE userID = %s AND threadID = %s''')
                        argList.append([status, userID, threadID.bytes])
                db.update(queryList, argList)


class User:
        @staticmethod
        def delete(userID=None):
                if userID is None:
                        raise ValueError("User.delete(1): userID argument is null")
                
                queryList = ['''DELETE FROM user
                                WHERE userID = %s''']
                argList = [[userID]]
                db.update(queryList, argList)

                CliqueMembership.delete(userID=userID)
                InviteCode.all_delete(userID)
                ThreadStatus.delete(userID=userID)
                UserConnection.delete(userID)
                UserPresence.delete(userID)
                UserSession.all_delete(userID)

        @staticmethod
        def count(online=False):
                if online:
                        cursor = db.query('''SELECT * FROM user_presence
                                        WHERE presence <> %s
                                        ''', [constants.UserPresence.OFFLINE.value])
                else:
                        cursor = db.query('''SELECT * FROM user''', None)
                return len(cursor.fetchall()) 

        @staticmethod
        def get(alias=None, userID=None):
                if alias is None and userID is None:
                        raise ValueError("User.get(2): both arguments are null")
                
                if alias is not None:
                        cursor = db.query('''SELECT * FROM user
                                        WHERE alias = %s
                                        ''', [alias])
                elif userID is not None:
                        cursor = db.query('''SELECT * FROM user
                                        WHERE userID = %s
                                        ''', [userID])
                return cursor.fetchone()

        @staticmethod
        def ID_get(alias):
                if alias is None:
                        raise ValueError("User.ID_get(1): alias argument is null")
                
                cursor = db.query('''SELECT * FROM user
                                WHERE alias = %s
                                ''', [alias])
                result = cursor.fetchone()
                if result is not None:
                        return result[constants.ProtocolKey.USER_ID]
                else:
                        return None

        @staticmethod
        def make(alias, email=None, name=None, password=None, salt=None):
                if alias is None:
                        raise ValueError("User.make(4): alias argument is null")
                elif password is None:
                        raise ValueError("User.make(4): password argument is null")

                queryList = ['''INSERT INTO user
                                (alias, email, name, password, salt)
                                VALUES (%s, %s, %s, %s, %s)''']
                argList = [[alias, email, name, password, salt]]
                cursor = db.update(queryList, argList)

                return cursor.lastrowid
        
        @staticmethod
        def password_update(userID, password, salt):
                if userID is None:
                        raise ValueError("User.password_update(3): userID argument is null")
                elif password is None:
                        raise ValueError("User.password_update(3): password argument is null")
                elif salt is None:
                        raise ValueError("User.password_update(3): salt argument is null")
                
                queryList = ['''UPDATE user
                                SET password = %s, salt = %s
                                WHERE userID = %s''']
                argList = [[password, salt, userID]]
                db.update(queryList, argList)

        @staticmethod
        def profile_update(userID, alias, name):
                if userID is None:
                        raise ValueError("User.profile_update(3): userID argument is null")
                elif alias is None:
                        raise ValueError("User.profile_update(3): alias argument is null")
                
                queryList = ['''UPDATE user
                                SET alias = %s, name = %s
                                WHERE userID = %s''']
                argList = [[alias, name, userID]]
                db.update(queryList, argList)

        @staticmethod
        def referrer_update(referrer, referee):
                if referrer is None:
                        raise ValueError("User.referrer_update(2): referrer argument is null")
                elif referee is None:
                        raise ValueError("User.referrer_update(2): referee argument is null")

                queryList = ['''UPDATE user
                                SET referrer = %s
                                WHERE userID = %s''']
                argList = [[referrer, referee]]
                db.update(queryList, argList)
        
        @staticmethod
        def suspend(userID, suspend):
                if userID is None:
                        raise ValueError("User.suspend(2): userID argument is null")
                elif suspend is None:
                        raise ValueError("User.suspend(2): suspend argument is null")
                
                queryList = ['''UPDATE user
                                SET suspended = %s
                                WHERE userID = %s''']
                argList = [[suspend, userID]]
                db.update(queryList, argList)


class UserConnection:
        @staticmethod
        def accept(initiatorID, targetID):
                if initiatorID is None:
                        raise ValueError("UserConnection.accept(2): initiatorID argument is null")
                elif targetID is None:
                        raise ValueError("UserConnection.accept(2): targetID argument is null")

                queryList = ['''UPDATE user_connection
                                SET status = %s
                                WHERE initiator = %s AND target = %s''']
                argList = [[constants.UserConnectionStatus.ESTABLISHED.value, initiatorID, targetID]]
                db.update(queryList, argList)

        # This will return a list of IDs, not a list of dicts.
        @staticmethod
        def all_get(userID, raw=False, limit=0):
                if userID is None:
                        raise ValueError("UserConnection.all_get(2): userID argument is null")
                
                if raw:
                        query = '''(SELECT target as userID, timestamp FROM user_connection WHERE initiator = %s AND status = %s)
                                UNION (SELECT initiator as userID, timestamp FROM user_connection WHERE target = %s AND status = %s)
                                ORDER BY timestamp DESC
                                '''
                else:
                        query = '''SELECT userID, alias, name FROM user
                                INNER JOIN user_connection
                                ON (user_connection.target = user.userID AND user_connection.initiator = %s AND user_connection.status = %s)
                                OR (user_connection.initiator = user.userID AND user_connection.target = %s AND user_connection.status = %s)
                                ORDER BY user_connection.timestamp DESC
                                '''
                paramList = [userID, constants.UserConnectionStatus.ESTABLISHED.value,
                    userID, constants.UserConnectionStatus.ESTABLISHED.value]
                if limit > 0:
                        query += " LIMIT %s"
                        paramList.append(limit)
                
                cursor = db.query(query, paramList)
                result = cursor.fetchall()
                if raw:
                        return [row[constants.ProtocolKey.USER_ID] for row in result]
                else:
                        return result
                
                
        @staticmethod
        def delete(userID):
                queryList = ['''DELETE FROM user_connection
                                WHERE initiator = %s OR target = %s''']
                argList = [[userID, userID]]
                db.update(queryList, argList)

        @staticmethod
        def exists(user1, user2):
                if user1 is None:
                        raise ValueError("UserConnection.exists(2): user1 argument is null")
                elif user2 is None:
                        raise ValueError("UserConnection.exists(2): user2 argument is null")

                cursor = db.query('''SELECT * FROM user_connection
                                WHERE (initiator = %s AND target = %s) OR (target = %s AND initiator =  %s)
                                ''', [user1, user2, user1, user2])
                result = cursor.fetchone()
                if result is not None:
                        return True
                else:
                        return False

        @staticmethod
        def make(initiatorID, targetID, status=constants.UserConnectionStatus.REQUESTED):
                if initiatorID is None:
                        raise ValueError("UserConnection.make(2): initiatorID argument is null")
                elif targetID is None:
                        raise ValueError("UserConnection.make(2): targetID argument is null")

                queryList = ['''INSERT INTO user_connection
                                (initiator, target, status)
                                VALUES (%s, %s, %s)''']
                argList = [[initiatorID, targetID, status.value]]
                db.update(queryList, argList)
        
        @staticmethod
        def mark(userID, status):
                if userID is None:
                        raise ValueError("UserConnection.mark(2): userID argument is null")

                queryList = ['''UPDATE user_connection
                                SET seen = %s
                                WHERE target = %s''']
                argList = [[status, userID]]
                db.update(queryList, argList)

        # This will return a list of IDs, not a list of dicts.
        @staticmethod
        def mutuals(user1, user2):
                if user1 is None:
                        raise ValueError("UserConnection.mutuals(2): user1 argument is null")
                elif user2 is None:
                        raise ValueError("UserConnection.mutuals(2): user2 argument is null")
                
                cursor = db.query('''SELECT DISTINCT userID FROM (
                                (SELECT target as userID FROM user_connection WHERE initiator = %s AND status = %s)
                                UNION (SELECT initiator as userID FROM user_connection WHERE target = %s AND status = %s)
                                ) AS user1 WHERE user1.userID IN (
                                (SELECT target as userID FROM user_connection WHERE initiator = %s AND status = %s)
                                UNION (SELECT initiator as userID FROM user_connection WHERE target = %s AND status = %s)
                                )
                                ''', [user1, constants.UserConnectionStatus.ESTABLISHED.value, user1, constants.UserConnectionStatus.ESTABLISHED.value, user2, constants.UserConnectionStatus.ESTABLISHED.value, user2, constants.UserConnectionStatus.ESTABLISHED.value])
                result = cursor.fetchall()
                return [row[constants.ProtocolKey.USER_ID] for row in result]

        @staticmethod
        def pending_requests_received_get(userID):
                if userID is None:
                        raise ValueError("UserConnection.pending_requests_received_get(1): userID argument is null")

                cursor = db.query('''SELECT initiator as userID, timestamp, seen FROM user_connection
                                WHERE target = %s AND status = %s
                                ''', [userID, constants.UserConnectionStatus.REQUESTED.value])
                return cursor.fetchall()
        
        @staticmethod
        def pending_requests_sent_get(userID):
                if userID is None:
                        raise ValueError("UserConnection.pending_requests_sent_get(1): userID argument is null")

                cursor = db.query('''SELECT target as userID, timestamp FROM user_connection
                                WHERE initiator = %s AND status = %s
                                ''', [userID, constants.UserConnectionStatus.REQUESTED.value])
                return cursor.fetchall()

        # Returns 20 of the user's newest connections over the past 7 days (by default).
        @staticmethod
        def recents(userID, days=7, limit=20):
                if userID is None:
                        raise ValueError("UserConnection.recents(3): userID argument is null")

                query = '''SELECT user.userID, user.alias, user_connection.timestamp FROM user
                        INNER JOIN user_connection
                        ON (user_connection.target = user.userID AND user_connection.initiator = %s AND user_connection.status = %s AND timestamp >= now() - INTERVAL %s DAY)
                        OR (user_connection.initiator = user.userID AND user_connection.target = %s AND user_connection.status = %s AND timestamp >= now() - INTERVAL %s DAY)
                        ORDER BY user_connection.timestamp DESC
                        LIMIT %s
                        '''
                cursor = db.query(query, [userID, constants.UserConnectionStatus.ESTABLISHED.value,
                            days, userID, constants.UserConnectionStatus.ESTABLISHED.value, days, limit])
                return cursor.fetchall()

        @staticmethod
        def remove(user1, user2):
                queryList = ['''DELETE FROM user_connection
                                WHERE (initiator = %s AND target = %s) OR (target = %s AND initiator =  %s)''']
                argList = [[user1, user2, user1, user2]]
                db.update(queryList, argList)


class UserPasswordReset:
        @staticmethod
        def delete(userID):
                if userID is None:
                        raise ValueError("UserPasswordReset.delete(1): userID argument is null")

                queryList = ['''DELETE FROM user_password_reset
                                WHERE userID = %s''']
                argList = [[userID]]
                db.update(queryList, argList)
        
        @staticmethod
        def get(userID=None, secret=None):
                if userID is None and secret is None:
                        raise ValueError("UserPasswordReset.get(2): both arguments are null")

                if userID is not None:
                        cursor = db.query('''SELECT * FROM user_password_reset
                                        WHERE userID = %s
                                        ''', [userID])
                else:
                        cursor = db.query('''SELECT * FROM user_password_reset
                                        WHERE secret = %s
                                        ''', [secret])

                return cursor.fetchone()
        
        @staticmethod
        def make(userID, secret):
                if userID is None:
                        raise ValueError("UserPasswordReset.make(2): userID argument is null")
                elif secret is None:
                        raise ValueError("UserPasswordReset.make(2): secret argument is null")

                queryList = ['''INSERT IGNORE INTO user_password_reset
                                (userID, secret)
                                VALUES (%s, %s)''']
                argList = [[userID, secret]]
                db.update(queryList, argList)


class UserPresence:
        @staticmethod
        def delete(userID):
                if userID is None:
                        raise ValueError("UserPresence.delete(1): userID argument is null")

                queryList = ['''DELETE FROM user_presence
                                WHERE userID = %s''']
                argList = [[userID]]
                db.update(queryList, argList)

        @staticmethod
        def make(userID, presence):
                if userID is None:
                        raise ValueError("UserPresence.make(2): userID argument is null")
                elif presence is None:
                        raise ValueError("UserPresence.make(2): presence argument is null")

                queryList = ['''INSERT IGNORE INTO user_presence
                                (userID, presence)
                                VALUES (%s, %s)''']
                argList = [[userID, presence.value]]
                db.update(queryList, argList)
        
        @staticmethod
        def update(userID, presence, target=None):
                if userID is None:
                        raise ValueError("UserPresence.update(3): userID argument is null")
                elif presence is None:
                        raise ValueError("UserPresence.update(3): presence argument is null")

                queryList = ['''UPDATE user_presence
                                SET presence = %s, target = %s, timestamp = CURRENT_TIMESTAMP
                                WHERE userID = %s''']
                argList = [[presence.value, target, userID]]
                db.update(queryList, argList)


class UserSession:
        @staticmethod
        def all_delete(userID):
                queryList = ['''DELETE FROM user_session
                                WHERE userID = %s''']
                argList = [[userID]]
                db.update(queryList, argList)
        
        @staticmethod
        def all_get(userID):
                if userID is None:
                        raise ValueError("UserSession.all_get(1): userID argument is null")
                
                cursor = db.query('''SELECT * FROM user_session
                                WHERE userID = %s
                                ''', [userID])
                return cursor.fetchall()
        
        @staticmethod
        def delete(sessionID):
                queryList = ['''DELETE FROM user_session
                                WHERE sessionID = %s''']
                argList = [[sessionID]]
                db.update(queryList, argList)

        @staticmethod
        def get(sessionID):
                if sessionID is None:
                        raise ValueError("UserSession.get(1): sessionID argument is null")
                
                cursor = db.query('''SELECT * FROM user_session
                                WHERE sessionID = %s
                                ''', [sessionID])
                return cursor.fetchone()

        @staticmethod
        def make(sessionID, userID, IPAddress):
                if sessionID is None:
                        raise ValueError("UserSession.make(3): sessionID argument is null")
                elif userID is None:
                        raise ValueError("UserSession.make(3): userID argument is null")
                elif IPAddress is None:
                        raise ValueError("UserSession.make(3): IPAddress argument is null")
                
                queryList = ['''INSERT IGNORE INTO user_session
                                (sessionID, userID, IPAddress)
                                VALUES (%s, %s, %s)''']
                argList = [[sessionID, userID, IPAddress]]
                db.update(queryList, argList)
        
        @staticmethod
        def update(sessionID, IPAddress):
                if sessionID is None:
                        raise ValueError("UserSession.update(2): sessionID argument is null")
                
                queryList = ['''UPDATE user_session
                                SET IPAddress = %s, timestamp = CURRENT_TIMESTAMP
                                WHERE sessionID = %s''']
                argList = [[IPAddress, sessionID]]
                db.update(queryList, argList)
