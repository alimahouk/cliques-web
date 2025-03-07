from flask import render_template, request, session

from app import models
from app.constants import ProtocolKey


def bad_request(e):
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                return render_template("pages/errors/400.html",
                                ProtocolKey=ProtocolKey,
                                user=user), 400
        else:
                return render_template("pages/errors/400.html",
                                user=None), 400


def auth_required(e):
        threadID = request.args.get("threadid")
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                return render_template("pages/errors/401.html",
                                ProtocolKey=ProtocolKey,
                                threadID=threadID,
                                user=user), 401
        else:
                return render_template("pages/errors/401.html",
                                ProtocolKey=ProtocolKey,
                                threadID=threadID,
                                user=None), 401


def forbidden(e):
        threadID = request.args.get("threadid")
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                return render_template("pages/errors/403.html",
                                ProtocolKey=ProtocolKey,
                                threadID=threadID,
                                user=user), 403
        else:
                return render_template("pages/errors/403.html",
                                ProtocolKey=ProtocolKey,
                                threadID=threadID,
                                user=None), 403


def page_not_found(e):
        if ProtocolKey.USER_ID in session:
                userID = session[ProtocolKey.USER_ID]
                user = models.User.get(userID=userID)
                return render_template("pages/errors/404.html",
                                ProtocolKey=ProtocolKey,
                                user=user), 404
        else:
                return render_template("pages/errors/404.html",
                                user=None), 404
        