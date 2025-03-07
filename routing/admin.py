import uuid

from flask import abort, redirect, render_template, request, session

from app import models
from app.constants import AdminError, ProtocolKey
from controllers import admin


def comment_erase():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        try:
                                commentID = uuid.UUID(request.form[ProtocolKey.COMMENT_ID])
                                result = admin.comment_erase(commentID)
                                if result != AdminError.OK:
                                        consolePath += "?error=" + result.value
                        except ValueError:
                                consolePath += "?error=" + str(AdminError.BAD_UUID.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)


def console():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        commentCount = models.Comment.count()
                        postCount = models.Post.count()
                        threadCount = models.Thread.count()
                        userCount = models.User.count()
                        userOnlineCount = models.User.count(online=True)

                        return render_template("pages/admin.html", 
                                commentCount=commentCount, 
                                postCount=postCount, 
                                threadCount=threadCount,
                                userCount=userCount,
                                userOnlineCount=userOnlineCount)
                else:
                        abort(404)
        else:
                abort(404)


def post_erase():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        try:
                                postID = uuid.UUID(request.form[ProtocolKey.POST_ID])
                                result = admin.post_erase(postID)
                                if result != AdminError.OK:
                                        consolePath += "?error=" + result.value
                        except ValueError:
                                consolePath += "?error=" + str(AdminError.BAD_UUID.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)


def thread_erase():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        try:
                                threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])
                                result = admin.thread_erase(threadID)
                                if result != AdminError.OK:
                                        consolePath += "?error=" + result.value
                        except ValueError:
                                consolePath += "?error=" + str(AdminError.BAD_UUID.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)

def thread_ghost():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        try:
                                threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])
                                ghost = int(request.form[ProtocolKey.GHOSTED])
                                
                                result = admin.thread_ghost(threadID, ghost)
                                if result != AdminError.OK:
                                        consolePath += "?error=" + result.value
                        except ValueError:
                                consolePath += "?error=" + str(AdminError.BAD_UUID.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)


def thread_lock():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        try:
                                threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])
                                lock = int(request.form[ProtocolKey.LOCKED])
                                
                                result = admin.thread_lock(threadID, lock)
                                if result != AdminError.OK:
                                        consolePath += "?error=" + result.value
                        except ValueError:
                                consolePath += "?error=" + str(AdminError.BAD_UUID.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)


def thread_modify():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        try:
                                description = request.form[ProtocolKey.THREAD_DESCRIPTION]
                                threadID = uuid.UUID(request.form[ProtocolKey.THREAD_ID])
                                title = request.form[ProtocolKey.THREAD_TITLE]
                                
                                result = admin.thread_modify(threadID, title, description)
                                if result != AdminError.OK:
                                        consolePath += "?error=" + result.value
                        except ValueError:
                                consolePath += "?error=" + str(AdminError.BAD_UUID.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)


def user_delete():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        
                        alias = request.form[ProtocolKey.ALIAS]
                        if request.form[ProtocolKey.USER_ID] is not None and len(request.form[ProtocolKey.USER_ID]) > 0:
                                userID = int(request.form[ProtocolKey.USER_ID])
                        else:
                                userID = None
                        
                        result = admin.user_delete(userID, alias)
                        if result != AdminError.OK:
                                consolePath += "?error=" + str(result.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)


def user_update():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        
                        alias = request.form[ProtocolKey.ALIAS]
                        name = request.form[ProtocolKey.NAME]
                        userID = int(request.form[ProtocolKey.USER_ID])
                        
                        result = admin.user_profile_update(userID, alias, name)
                        if result != AdminError.OK:
                                consolePath += "?error=" + str(result.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)


def user_suspend():
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                if user[ProtocolKey.ADMIN] == 1:
                        consolePath = "/admin"
                        
                        alias = request.form[ProtocolKey.ALIAS]
                        if request.form[ProtocolKey.USER_ID] is not None and len(request.form[ProtocolKey.USER_ID]) > 0:
                                userID = int(request.form[ProtocolKey.USER_ID])
                        else:
                                userID = None
                        suspend = int(request.form[ProtocolKey.SUSPENDED])
                        
                        result = admin.user_suspend(userID, alias, suspend)
                        if result != AdminError.OK:
                                consolePath += "?error=" + str(result.value)

                        return redirect(consolePath)
                else:
                        abort(404)
        else:
                abort(404)
