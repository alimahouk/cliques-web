import re

from app import models
from app.constants import AdminError, ProtocolKey
from controllers import identity


def comment_erase(commentID):
        if commentID is None:
                return AdminError.BAD_REQUEST
        models.Comment.erase(commentID=commentID)
        return AdminError.OK


def post_erase(postID):
        if postID is None:
                return AdminError.BAD_REQUEST
        models.Comment.erase(postID=postID)
        models.Post.erase(postID=postID)
        return AdminError.OK


def thread_erase(threadID):
        if threadID is None:
                return AdminError.BAD_REQUEST
        # Deletes a thread and all posts and comments attached to it.
        posts = models.Post.all_get(threadID, limit=0)
        for post in posts:
                postID = post[ProtocolKey.POST_ID]
                models.Comment.erase(postID=postID)

        models.Post.erase(threadID=threadID)
        models.Thread.erase(threadID)
        return AdminError.OK


def thread_ghost(threadID, ghost):
        if threadID is None:
                return AdminError.BAD_REQUEST
        models.Thread.ghost(threadID, ghost)
        return AdminError.OK


def thread_lock(threadID, lock):
        if threadID is None:
                return AdminError.BAD_REQUEST
        models.Thread.lock(threadID, lock)
        return AdminError.OK


def thread_modify(threadID, title, description):
        if threadID is None or title is None:
                return AdminError.BAD_REQUEST
        
        title = title.strip()
        if title is None or len(title) == 0 or len(title) > 140:
                return AdminError.INVALID_THREAD_TITLE
        elif len(description) > 10000:
                return AdminError.INVALID_THREAD_DESCRIPTION

        models.Thread.modify(threadID, title, description)
        return AdminError.OK


def user_delete(userID, alias):
        if userID is None and alias is None:
                return AdminError.BAD_REQUEST
        if userID is None:
                alias = alias.strip()
                user = models.User.get(alias=alias)
                if user:
                        userID = user[ProtocolKey.USER_ID]
                else:
                        return AdminError.NOT_FOUND
        models.User.delete(userID)
        return AdminError.OK


def user_profile_update(userID, alias, name):
        if userID is None or alias is None:
                return AdminError.BAD_REQUEST
        alias = alias.strip()

        user = models.User.get(userID=userID)

        if len(alias) < 2 or len(alias) > 64:
                return AdminError.INVALID_ALIAS
        elif re.match(r"^(?!.*[-.]$)[-\w\.]+$", alias) is None:
                return AdminError.INVALID_ALIAS
        elif user[ProtocolKey.ALIAS] != alias and identity.alias_exists(alias):
                return AdminError.EXISTS

        if alias.lower() in identity.reservedAliases:
                return AdminError.EXISTS

        if name is not None:
                # Sanitisation
                name = name.strip()
                if len(name) > 64:
                        return AdminError.INVALID_NAME
        
        models.User.profile_update(userID, alias, name)
        return AdminError.OK


def user_suspend(userID, alias, suspend):
        if (userID is None and alias is None) or suspend is None:
                return AdminError.BAD_REQUEST
        if userID is None:
                alias = alias.strip()
                user = models.User.get(alias=alias)
                if user:
                        userID = user[ProtocolKey.USER_ID]
                else:
                        return AdminError.NOT_FOUND
        if suspend:
                models.UserSession.all_delete(userID)
        models.User.suspend(userID, suspend)
        return AdminError.OK
