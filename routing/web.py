import re
import urllib.parse
import uuid
from datetime import datetime, timedelta

from flask import abort, redirect, render_template, request, session
from flask_mail import Message

from app import mail, models
from app.constants import (ConnectivityError, ContentError, GroupType,
                           ProtocolKey, SignupFormStatus, ThreadType,
                           UserError)
from controllers import cliques, connectivity, content, identity


def about():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                user = models.User.get(userID=userID)
        else:
                user = None
        
        now = datetime.now()

        return render_template("pages/about.html",
                        copyrightYear=now.year,
                        ProtocolKey=ProtocolKey,
                        user=user)


def clique():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                if "cliqueid" in request.args:
                        cliqueID = request.args.get("cliqueid")
                else:
                        abort(400)
                
                members = models.CliqueMembership.all_get(cliqueID)
                now = datetime.now()
                response = content.clique_threads_get(userID, cliqueID)
                threads = response.body
                user = models.User.get(userID=userID)
                
                for thread in threads:
                        dateCreated = thread[ProtocolKey.CREATION_DATE]
                        thread[ProtocolKey.CREATION_DATE] = dateCreated.astimezone().isoformat()

                        if ProtocolKey.LAST_MODIFICATION_DATE in thread:
                                dateModified = thread[ProtocolKey.LAST_MODIFICATION_DATE]
                                thread[ProtocolKey.LAST_MODIFICATION_DATE] = dateModified.astimezone().isoformat()

                        if ProtocolKey.THREAD_ID in thread:
                                threadID = thread[ProtocolKey.THREAD_ID]
                                thread[ProtocolKey.THREAD_ID] = str(threadID)
                        
                        if thread[ProtocolKey.THREAD_TYPE] == ThreadType.PLAIN:
                                # Preprocess the title.
                                if ProtocolKey.THREAD_TITLE in thread and \
                                   thread[ProtocolKey.THREAD_TITLE] is not None:
                                        if len(thread[ProtocolKey.THREAD_TITLE]) > 0:
                                                title = thread[ProtocolKey.THREAD_TITLE]
                                                thread[ProtocolKey.THREAD_TITLE_RAW] = title

                                                # The following preprocessing must be carried out in this specific order!
                                                # 1) Fix ampersands.
                                                title = content.html_ampersands(title)
                                                # 2) Escape angled brackets.
                                                title = content.html_angled_brackets(title)
                                                thread[ProtocolKey.THREAD_TITLE] = title
                                        else:
                                                thread[ProtocolKey.THREAD_TITLE] = None

                                # Preprocess the description.
                                if ProtocolKey.THREAD_DESCRIPTION in thread and \
                                   thread[ProtocolKey.THREAD_DESCRIPTION] is not None:
                                        if len(thread[ProtocolKey.THREAD_DESCRIPTION]) > 0:
                                                description = thread[ProtocolKey.THREAD_DESCRIPTION]
                                                # Fix ampersands.
                                                description = content.html_ampersands(description)
                                                # Escape angled brackets!
                                                description = content.html_angled_brackets(description)
                                                maxLen = 140
                                                thread[ProtocolKey.THREAD_DESCRIPTION] = (description[:maxLen] + "…") if len(description) > maxLen else description
                                        else:
                                                thread[ProtocolKey.THREAD_DESCRIPTION] = None
                        elif thread[ProtocolKey.THREAD_TYPE] == ThreadType.CONNECTION_UPDATE:
                                # This is a special kind of thread that uses just-in-time-crafted body text.
                                connections = thread[ProtocolKey.THREAD_DESCRIPTION]
                                if userID == thread[ProtocolKey.AUTHOR][ProtocolKey.USER_ID]:
                                        thread[ProtocolKey.AUTHOR] = "You"
                                else:
                                        thread[ProtocolKey.AUTHOR] = thread[ProtocolKey.AUTHOR][ProtocolKey.ALIAS]
                                
                                if len(connections) == 1:
                                        connection = connections[0]
                                        if connection[ProtocolKey.USER_ID] == userID:
                                                connectionDisplay = "<span class=\"currentUser\">you</span>"
                                        else:
                                                connectionDisplay = connection[ProtocolKey.ALIAS]

                                        headline = "connected with " + connectionDisplay + "."
                                elif len(connections) == 2:
                                        connection1 = connections[0]
                                        connection2 = connections[1]
                                        if connection1[ProtocolKey.USER_ID] == userID:
                                                connection1Display = "<span class=\"currentUser\">you</span>"
                                        else:
                                                connection1Display = connection1[ProtocolKey.ALIAS]

                                        if connection2[ProtocolKey.USER_ID] == userID:
                                                connection2Display = "<span class=\"currentUser\">you</span>"
                                        else:
                                                connection2Display = connection2[ProtocolKey.ALIAS]

                                        headline = "connected with " + connection1Display + " &amp; " + connection2Display + "."
                                elif len(connections) > 2:
                                        connection1 = connections[0]
                                        connection2 = connections[1]
                                        if connection1[ProtocolKey.USER_ID] == userID:
                                                connection1Display = "<span class=\"currentUser\">you</span>"
                                        else:
                                                connection1Display = connection1[ProtocolKey.ALIAS]

                                        if connection2[ProtocolKey.USER_ID] == userID:
                                                connection2Display = "<span class=\"currentUser\">you</span>"
                                        else:
                                                connection2Display = connection2[ProtocolKey.ALIAS]

                                        headline = "connected with " + connection1Display + ", " + connection2Display + ", &amp; " + (connections.length - 2) + " other " + ("person" if len(connections) == 3 else "people")  + "."

                                thread[ProtocolKey.THREAD_DESCRIPTION] = headline

                return render_template("pages/clique.html",
                                copyrightYear=now.year,
                                cliqueID=cliqueID,
                                members=members,
                                ProtocolKey=ProtocolKey,
                                threads=threads,
                                ThreadType=ThreadType,
                                user=user)
        else:
                abort(401)


def community():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                user = models.User.get(userID=userID)
        else:
                user = None

        now = datetime.now()
        
        return render_template("pages/community.html",
                        copyrightYear=now.year,
                        ProtocolKey=ProtocolKey,
                        user=user)


def connection_accept():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)
                
                initiatorID = int(request.form[ProtocolKey.USER_ID])
                response = connectivity.request_accept(initiatorID, userID)
                if response.errorCode == ConnectivityError.OK:
                        return redirect("/connections")
                else:
                        abort(500)
        else:
                abort(401)


def connection_add():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                if request.method == "POST":
                        targetAlias = request.form[ProtocolKey.ALIAS]
                        response = connectivity.request_make(userID, targetAlias)
                        if response.errorCode == ConnectivityError.OK:
                                return redirect("/")
                        else:
                                path = "/connections/add?connectivityerr=" + str(ConnectivityError.NOT_FOUND.value)
                                return redirect(path)
                else:
                        connectivityErrorMessage = None
                        error = None

                        if "connectivityerr" in request.args:
                                error = int(request.args.get("connectivityerr"))
                        
                        if error == ConnectivityError.NOT_FOUND:
                                connectivityErrorMessage = "No user with this username exists!"

                        now = datetime.now()
                        user = models.User.get(userID=userID)
                        return render_template("pages/add_connection.html",
                                connectivityErrorMessage=connectivityErrorMessage,
                                copyrightYear=now.year,
                                ProtocolKey=ProtocolKey,
                                user=user)
        else:
                abort(401)


def connection_remove():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                targetID = int(request.form[ProtocolKey.USER_ID])
                connectivity.connection_remove(userID, targetID)
                return redirect("/connections")
        else:
                abort(401)


def connection_requests():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                connectionRequestsReceived = connectivity.requests_received_get(userID)
                now = datetime.now()
                user = models.User.get(userID=userID)
                return render_template("pages/connection_requests_list.html",
                                connectionRequestsReceived=connectionRequestsReceived,
                                copyrightYear=now.year,
                                ProtocolKey=ProtocolKey,
                                user=user)
        else:
                abort(401)


def connections():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                connectionRequestsReceived = models.UserConnection.pending_requests_received_get(userID)
                connections = models.UserConnection.all_get(userID)
                now = datetime.now()
                user = models.User.get(userID=userID)
                return render_template("pages/connections_list.html",
                                connectionRequestsReceivedCount=len(connectionRequestsReceived),
                                connections=connections,
                                copyrightYear=now.year,
                                ProtocolKey=ProtocolKey,
                                user=user)
        else:
                abort(401)


def contact():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                user = models.User.get(userID=userID)
        else:
                user = None
                
        now = datetime.now()

        if request.method == "POST":
                senderAddress = request.form["replyTo"]
                body = request.form["message"]

                if senderAddress is not None and not content.is_valid_email(senderAddress):
                        senderAddress = None
                
                if body is not None:
                        body = body.strip()
                        if len(body) == 0:
                                body = None

                if senderAddress is not None and body is not None:
                        msg = Message("Contact Submission",
                                        sender=("Cliques", "postmaster@alimahouk.com"), 
                                        recipients=["cliques@alimahouk.com"],
                                        reply_to=senderAddress)
                        msg.body = body
                        mail.send(msg)
                        return redirect("https://alimahouk.com")
                else:
                        return render_template("pages/contact.html",
                                        copyrightYear=now.year,
                                        ProtocolKey=ProtocolKey,
                                        user=user)
        else:
                return render_template("pages/contact.html",
                                copyrightYear=now.year,
                                ProtocolKey=ProtocolKey,
                                user=user)


def index():
        now = datetime.now()

        # Check if there's an invite code in the URL.
        inviteCode = request.args.get("invite")
        if inviteCode is not None and len(inviteCode) <= 64:
                # Strip potential hazards.
                inviteCode = inviteCode.replace("\"", "")
                inviteCode = inviteCode.replace("'", "")
                inviteCode = inviteCode.replace("`", "")
        else:
                inviteCode = None
                
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")
                
                if inviteCode is not None:
                        connectivity.invite_connection_make(userID, inviteCode)
                        # Redirect to a clean homepage URL to get rid of the invite code.
                        return redirect("/")
                else:
                        # Update session details.
                        IPAddress = identity.ip_address(request)
                        models.UserSession.update(sessionID, IPAddress)
                        
                        cliqueList = cliques.cliques_get(userID, raw=False, stripUser=True)
                        connectionRequestsReceived = models.UserConnection.pending_requests_received_get(userID)
                        connections = models.UserConnection.all_get(userID)
                        user = models.User.get(userID=userID)
                        return render_template("pages/cliques_list.html", 
                                cliques=cliqueList,
                                connectionCount=len(connections),
                                connectionRequestsReceivedCount=len(connectionRequestsReceived),
                                copyrightYear=now.year,
                                ProtocolKey=ProtocolKey,
                                user=user)
        else:
                roomID = content.lr_room_id_get(request)
                currentRoom = models.LivingRoom.get(roomID)
                if roomID is None or \
                   currentRoom is None:
                        # Unsupported country; use the first country in the supported list.
                        allRooms = models.LivingRoom.all_get()
                        if len(allRooms) > 0:
                                currentRoom = allRooms[0]
                                roomID = currentRoom[ProtocolKey.ROOM_ID]

                response = content.lr_threads_get(None, roomID)
                threads = response.body[ProtocolKey.THREADS]
                for thread in threads:
                        dateCreated = thread[ProtocolKey.CREATION_DATE]
                        dateModified = thread[ProtocolKey.LAST_MODIFICATION_DATE]
                        threadID = thread[ProtocolKey.THREAD_ID]

                        thread[ProtocolKey.CREATION_DATE] = dateCreated.astimezone().isoformat()
                        thread[ProtocolKey.LAST_MODIFICATION_DATE] = dateModified.astimezone().isoformat()
                        thread[ProtocolKey.THREAD_ID] = str(threadID)

                        if thread[ProtocolKey.THREAD_TYPE] == ThreadType.PLAIN:
                                # Preprocess the title.
                                if ProtocolKey.THREAD_TITLE in thread and \
                                   thread[ProtocolKey.THREAD_TITLE] is not None:
                                        if len(thread[ProtocolKey.THREAD_TITLE]) > 0:
                                                title = thread[ProtocolKey.THREAD_TITLE]
                                                thread[ProtocolKey.THREAD_TITLE_RAW] = title

                                                # The following preprocessing must be carried out in this specific order!
                                                # 1) Fix ampersands.
                                                title = content.html_ampersands(title)
                                                # 2) Escape angled brackets.
                                                title = content.html_angled_brackets(title)
                                                thread[ProtocolKey.THREAD_TITLE] = title
                                        else:
                                                thread[ProtocolKey.THREAD_TITLE] = None

                                # Preprocess the description.
                                if ProtocolKey.THREAD_DESCRIPTION in thread and \
                                   thread[ProtocolKey.THREAD_DESCRIPTION] is not None:
                                        if len(thread[ProtocolKey.THREAD_DESCRIPTION]) > 0:
                                                description = thread[ProtocolKey.THREAD_DESCRIPTION]
                                                # Fix ampersands.
                                                description = content.html_ampersands(description)
                                                # Escape angled brackets!
                                                description = content.html_angled_brackets(description)
                                                maxLen = 140
                                                thread[ProtocolKey.THREAD_DESCRIPTION] = (description[:maxLen] + "…") if len(description) > maxLen else description
                                        else:
                                                thread[ProtocolKey.THREAD_DESCRIPTION] = None

                return render_template("pages/lr.html",
                                copyrightYear=now.year,
                                currentRoom=currentRoom,
                                ProtocolKey=ProtocolKey,
                                threads=threads,
                                ThreadType=ThreadType,
                                user=None)


def login():
        now = datetime.now()
        path = "/login"

        # If there's an invite code in the URL then be sure to propagate it
        # across error pages to the user's home page.
        inviteCode = request.args.get("invite")
        if inviteCode is not None and \
           len(inviteCode) <= 64:
                # Strip potential hazards.
                inviteCode = inviteCode.replace("\"", "")
                inviteCode = inviteCode.replace("'", "")
                inviteCode = inviteCode.replace("`", "")
                path += f"?invite={inviteCode}"
        else:
                inviteCode = None
        
        # The user could've been sent to login via an action that requires it.
        # Store the threadid to redirect them back to it.
        threadID = request.args.get("threadid")

        if request.method == "POST":
                if threadID is not None:
                        path = "/scape"
                else:
                        path = "/"
                        
                
                if inviteCode is not None:
                        path += f"?invite={inviteCode}"
                if threadID is not None:
                        path += f"?threadid={threadID}"

                if ProtocolKey.USER_ID in session: # Already logged in.
                        return redirect(path)
                
                alias = request.form[ProtocolKey.ALIAS]
                password = request.form[ProtocolKey.PASSWORD]

                result = identity.login(alias, password)
                if result == identity.LoginStatus.OK:
                        IPAddress = identity.ip_address(request)
                        sessionID = identity.session_id_generate()
                        userID = models.User.ID_get(alias)

                        models.UserSession.make(sessionID, userID, IPAddress)
                        session[ProtocolKey.SESSION_ID] = sessionID
                        session[ProtocolKey.USER_ID] = userID
                        session.permanent = True
                        return redirect(path)
                else:
                        path = f"/login?loginerr={result}&loginalias={urllib.parse.quote(alias)}"
                        if inviteCode is not None:
                                path += f"&invite={inviteCode}"
                        if threadID is not None:
                                path += f"&threadid={threadID}"
                        # Return the entered username to display in the form.
                        return redirect(path)
        else:
                if ProtocolKey.USER_ID in session: # Already logged in.
                        return redirect("/")

                loginAlias = request.args.get("loginalias")
                loginError = request.args.get("loginerr")
                loginErrorMessage = None
                signupAlias = request.args.get("signupalias")
                signupError = request.args.get("signuperr")
                signupErrorMessage = None
                signupName = request.args.get("name")

                if loginError is not None:
                        loginError = int(loginError)
                        if loginError == identity.LoginStatus.ERR_INVALID_ALIAS:
                                loginErrorMessage = "The username you entered is invalid!"
                        elif loginError == identity.LoginStatus.ERR_INVALID_PASSWORD:
                                loginErrorMessage = "The password you entered is invalid!"
                        elif loginError == identity.LoginStatus.ERR_CREDENTIALS:
                                loginErrorMessage = "Your username/password combo is incorrect!"
                        elif loginError == identity.LoginStatus.ERR_NOTFOUND:
                                loginErrorMessage = "No account exists for this username!"
                        elif loginError == identity.LoginStatus.ERR_SUSPENDED:
                                loginErrorMessage = "Unfortunately, this account has been suspended!"
                elif signupError is not None:
                        signupError = int(signupError)
                        if signupError == identity.SignupStatus.ERR_BAN:
                                signupErrorMessage = "Oops, an error occurred."
                        elif signupError == identity.SignupStatus.ERR_INVALID_ALIAS:
                                signupErrorMessage = "The username you entered is invalid! A username must be at least 2 characters long."
                        elif signupError == identity.SignupStatus.ERR_INVALID_EMAIL:
                                signupErrorMessage = "The email address you entered is invalid!"
                        elif signupError == identity.SignupStatus.ERR_INVALID_NAME:
                                signupErrorMessage = "The name you entered is invalid!"
                        elif signupError == identity.SignupStatus.ERR_INVALID_PASSWORD:
                                signupErrorMessage = "The password you entered is invalid! A password must be at least 8 characters long."
                        elif signupError == identity.SignupStatus.ERR_EXISTS:
                                signupErrorMessage = "The username you picked already exists!"

                return render_template("pages/login.html", 
                        copyrightYear=now.year,
                        inviteCode=inviteCode,
                        loginAlias=loginAlias,
                        loginErrorMessage=loginErrorMessage,
                        ProtocolKey=ProtocolKey,
                        signupAlias=signupAlias,
                        signupName=signupName,
                        signupErrorMessage=signupErrorMessage,
                        signupFormStatus=SignupFormStatus.OPEN,
                        SignupFormStatus=SignupFormStatus,
                        threadID=threadID,
                        user=None)


def logout():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                models.UserSession.delete(sessionID)

                # Delete the cookie.
                [session.pop(key) for key in list(session.keys())]
        return redirect("/")


def lr(country):
        now = datetime.now()

        if country is None:
                roomID = content.lr_room_id_get(request)
        else:
                roomID = country
        homeRoomID = content.lr_room_id_get(request)

        currentRoom = models.LivingRoom.get(roomID)
        homeRoom = models.LivingRoom.get(homeRoomID)
        if roomID is None or \
           currentRoom is None:
                # Unsupported country; use the first country in the supported list.
                allRooms = models.LivingRoom.all_get()
                if len(allRooms) > 0:
                        currentRoom = allRooms[0]
                        roomID = currentRoom[ProtocolKey.ROOM_ID]

        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                user = models.User.get(userID=userID)
        else:
                user = None

        response = content.lr_threads_get(None, roomID)
        threads = response.body[ProtocolKey.THREADS]
        for thread in threads:
                dateCreated = thread[ProtocolKey.CREATION_DATE]
                dateModified = thread[ProtocolKey.LAST_MODIFICATION_DATE]
                threadID = thread[ProtocolKey.THREAD_ID]

                thread[ProtocolKey.CREATION_DATE] = dateCreated.astimezone().isoformat()
                thread[ProtocolKey.LAST_MODIFICATION_DATE] = dateModified.astimezone().isoformat()
                thread[ProtocolKey.THREAD_ID] = str(threadID)

                if thread[ProtocolKey.THREAD_TYPE] == ThreadType.PLAIN:
                        # Preprocess the title.
                        if ProtocolKey.THREAD_TITLE in thread and \
                           thread[ProtocolKey.THREAD_TITLE] is not None:
                                if len(thread[ProtocolKey.THREAD_TITLE]) > 0:
                                        title = thread[ProtocolKey.THREAD_TITLE]
                                        thread[ProtocolKey.THREAD_TITLE_RAW] = title

                                        # The following preprocessing must be carried out in this specific order!
                                        # 1) Fix ampersands.
                                        title = content.html_ampersands(title)
                                        # 2) Escape angled brackets.
                                        title = content.html_angled_brackets(title)
                                        thread[ProtocolKey.THREAD_TITLE] = title
                                else:
                                        thread[ProtocolKey.THREAD_TITLE] = None

                        # Preprocess the description.
                        if ProtocolKey.THREAD_DESCRIPTION in thread and \
                           thread[ProtocolKey.THREAD_DESCRIPTION] is not None:
                                if len(thread[ProtocolKey.THREAD_DESCRIPTION]) > 0:
                                        description = thread[ProtocolKey.THREAD_DESCRIPTION]
                                        # Fix ampersands.
                                        description = content.html_ampersands(description)
                                        # Escape angled brackets!
                                        description = content.html_angled_brackets(description)
                                        maxLen = 140
                                        thread[ProtocolKey.THREAD_DESCRIPTION] = (description[:maxLen] + "…") if len(description) > maxLen else description
                                else:
                                        thread[ProtocolKey.THREAD_DESCRIPTION] = None

        return render_template("pages/lr.html", 
                        copyrightYear=now.year, 
                        currentRoom=currentRoom,
                        homeRoom=homeRoom,
                        ProtocolKey=ProtocolKey,
                        threads=threads,
                        ThreadType=ThreadType,
                        user=user)

def lr_list():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)
                
                user = models.User.get(userID=userID)
        else:
                user = None
        
        now = datetime.now()
        rooms = content.lr_all_get()

        return render_template("pages/lr_list.html", 
                        copyrightYear=now.year,
                        ProtocolKey=ProtocolKey,
                        rooms=rooms,
                        user=user)


def password_forgot():
        if request.method == "POST":
                alias = request.form[ProtocolKey.ALIAS]
                email = request.form[ProtocolKey.EMAIL_ADDRESS]
                response = identity.password_reset_send_email(alias, email)

                return redirect("/forgot?usererr=" + str(response.value))
        else:
                userErrorMessage = None
                error = None
                now = datetime.now()

                if "passwordid" in request.args:
                        secret = request.args.get("passwordid")
                        resetData = models.UserPasswordReset.get(secret=secret)
                        
                        if resetData is not None and \
                           resetData[ProtocolKey.SECRET] == secret and \
                           now-timedelta(hours=1) <= resetData[ProtocolKey.TIMESTAMP] <= now:
                                userID = resetData[ProtocolKey.USER_ID]

                                if "usererr" in request.args:
                                        error = int(request.args.get("usererr"))

                                if error == UserError.ERR_INVALID_PASSWORD:
                                        userErrorMessage = "The password you entered is invalid! A password must be at least 8 characters long."
                                elif error == UserError.EXPIRED_LINK:
                                        userErrorMessage = "This password reset link has expired! Try resetting it again."

                                return render_template("pages/password_reset.html",
                                        copyrightYear=now.year,
                                        resetMode=True,
                                        secret=secret,
                                        userErrorMessage=userErrorMessage,
                                        userID=userID)
                        else:
                                userErrorMessage = "This password reset link has expired! Try resetting it again."

                                return render_template("pages/password_reset.html",
                                        userErrorMessage=userErrorMessage,
                                        copyrightYear=now.year)
                else:
                        if "usererr" in request.args:
                                error = int(request.args.get("usererr"))

                        if error == UserError.OK:
                                userErrorMessage = "Check your email for further instructions to help you reset your password."
                        elif error == UserError.NOT_FOUND:
                                userErrorMessage = "No user with this username/email address combination exists!"

                        return render_template("pages/password_reset.html",
                                copyrightYear=now.year,
                                userErrorMessage=userErrorMessage,  
                                user=None)


def password_reset():
        if ProtocolKey.PASSWORD not in request.form or \
           ProtocolKey.SECRET not in request.form or \
           ProtocolKey.USER_ID not in request.form:
                abort(400)

        password = request.form[ProtocolKey.PASSWORD]
        secret = request.form[ProtocolKey.SECRET]
        userID = int(request.form[ProtocolKey.USER_ID])
        response = identity.password_reset(userID, password, secret)

        if response == UserError.OK:
                return redirect("/login")
        else:
                return redirect(f"/forgot?passwordid={secret}&usererr={response.value}")
        

def privacy():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                user = models.User.get(userID=userID)
        else:
                user = None

        now = datetime.now()

        return render_template("pages/privacy.html",
                        copyrightYear=now.year,
                        ProtocolKey=ProtocolKey,
                        user=user)


def scape():
        threadID = request.args.get("threadid")

        try:
                threadID = uuid.UUID(threadID)
        except ValueError:
                abort(400)
        
        if "submissionerr" in request.args:
                error = int(request.args.get("submissionerr"))
        else:
                error = None
        
        now = datetime.now()
        submissionErrorMessage = None
        thread = None
        user = None
        userID = None

        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                user = models.User.get(userID=userID)
        
        threadResponse = content.thread_get(threadID, userID)
        if threadResponse is not None:
                if threadResponse.errorCode == ContentError.FORBIDDEN:
                        if user is not None:
                                abort(403)
                        else:
                                abort(401)
                elif threadResponse.errorCode == ContentError.NOT_FOUND:
                        abort(404)
                
                thread = threadResponse.body

                if thread[ProtocolKey.THREAD_TYPE] == ThreadType.PLAIN:
                        # Preprocess the title.
                        if ProtocolKey.THREAD_TITLE in thread and \
                           thread[ProtocolKey.THREAD_TITLE] is not None:
                                if len(thread[ProtocolKey.THREAD_TITLE]) > 0:
                                        title = thread[ProtocolKey.THREAD_TITLE]
                                        thread[ProtocolKey.THREAD_TITLE_RAW] = title

                                        # The following preprocessing must be carried out in this specific order!
                                        # 1) Fix ampersands.
                                        title = content.html_ampersands(title)
                                        # 2) Escape angled brackets.
                                        title = content.html_angled_brackets(title)
                                        thread[ProtocolKey.THREAD_TITLE] = title
                                else:
                                        thread[ProtocolKey.THREAD_TITLE] = None

                        # Preprocess the description.
                        if ProtocolKey.THREAD_DESCRIPTION in thread and \
                           thread[ProtocolKey.THREAD_DESCRIPTION] is not None:
                                if len(thread[ProtocolKey.THREAD_DESCRIPTION]) > 0:
                                        description = thread[ProtocolKey.THREAD_DESCRIPTION]

                                        # The following preprocessing must be carried out in this specific order!
                                        # 1) Fix ampersands.
                                        description = content.html_ampersands(description)
                                        # 2) Escape angled brackets.
                                        description = content.html_angled_brackets(description)

                                        # The raw description is clean of any HTML save for escaping dangerous stuff.
                                        thread[ProtocolKey.THREAD_DESCRIPTION_RAW] = description

                                        # 3) Parse quotes.
                                        description = content.html_quotes(description, "&gt;")
                                        # 4) Convert newlines into <br> tags.
                                        description = content.html_newlines(description)
                                        # 5) Convert URLs into <a> tags.
                                        description = content.html_urls(description)

                                        thread[ProtocolKey.THREAD_DESCRIPTION] = description
                                else:
                                        thread[ProtocolKey.THREAD_DESCRIPTION] = None

                dateCreated = thread[ProtocolKey.CREATION_DATE]
                dateModified = thread[ProtocolKey.LAST_MODIFICATION_DATE]
                threadID = thread[ProtocolKey.THREAD_ID]

                thread[ProtocolKey.CREATION_DATE] = dateCreated.astimezone().isoformat()
                thread[ProtocolKey.LAST_MODIFICATION_DATE] = dateModified.astimezone().isoformat()
                thread[ProtocolKey.THREAD_ID] = str(threadID)

                posts = thread[ProtocolKey.POSTS]
                for post in posts:
                        body = post[ProtocolKey.POST_BODY]

                        # The following preprocessing must be carried out in this specific order!
                        # 1) Escape angled brackets.
                        body = content.html_angled_brackets(body)
                        # 2) Parse quotes.
                        body = content.html_quotes(body, "&gt;")
                        # 3) Convert newlines into <br> tags.
                        body = content.html_newlines(body)
                        # 4) Convert URLs into <a> tags.
                        body = content.html_urls(body)

                        dateCreated = post[ProtocolKey.CREATION_DATE]
                        dateModified = post[ProtocolKey.LAST_MODIFICATION_DATE]
                        postID = post[ProtocolKey.POST_ID]

                        post[ProtocolKey.CREATION_DATE] = dateCreated.astimezone().isoformat()
                        post[ProtocolKey.LAST_MODIFICATION_DATE] = dateModified.astimezone().isoformat()
                        post[ProtocolKey.POST_BODY] = body
                        post[ProtocolKey.POST_ID] = str(postID)

        if error is not None:
                if error == ContentError.FORBIDDEN:
                        submissionErrorMessage = "You don't have the required permission to participate in this dialogue!"
                elif error == ContentError.INVALID_POST_BODY:
                        submissionErrorMessage = "A post can't be more than 10,000 characters long."

        return render_template("pages/scape.html", 
                        copyrightYear=now.year,
                        ProtocolKey=ProtocolKey,
                        submissionErrorMessage=submissionErrorMessage,
                        thread=thread,
                        user=user)


def signup():
        path = "/login"

        # If there's an invite code in the URL then be sure to propagate it
        # across error pages to the user's home page.
        inviteCode = request.args.get("invite")
        if inviteCode is not None and len(inviteCode) <= 64:
                # Strip potential hazards.
                inviteCode.replace("\"", "")
                inviteCode.replace("'", "")
                inviteCode.replace("`", "")
        else:
                inviteCode = None

        # The user could've been sent to login via an action that requires it.
        # Store the threadid to redirect them back to it.
        threadID = request.args.get("threadid")

        if request.method == "POST":
                if threadID is not None:
                        path = "/scape"
                else:
                        path = "/"

                if inviteCode is not None:
                        path += f"?invite={inviteCode}"
                if threadID is not None:
                        path += f"?threadid={threadID}"

                if ProtocolKey.USER_ID in session: # Already logged in.
                        return redirect(path)

                alias = request.form[ProtocolKey.ALIAS]
                email = request.form[ProtocolKey.EMAIL_ADDRESS]
                name = request.form[ProtocolKey.NAME]
                password = request.form[ProtocolKey.PASSWORD]

                result = identity.signup(alias, email, name, password)
                if result == identity.SignupStatus.OK:
                        # LOG
                        msg = Message("New Signup",
                                        sender=("Cliques", "postmaster@alimahouk.com"), 
                                        recipients=["cliques@alimahouk.com"])
                        msg.body = "@" + alias + " just joined!"
                        mail.send(msg)

                        IPAddress = identity.ip_address(request)
                        sessionID = identity.session_id_generate()
                        userID = models.User.ID_get(alias)

                        models.UserSession.make(sessionID, userID, IPAddress)
                        session[ProtocolKey.SESSION_ID] = sessionID
                        session[ProtocolKey.USER_ID] = userID
                        session.permanent = True
                        return redirect(path)
                else:
                        path = f"/login?signuperr={result}&signupalias={urllib.parse.quote(alias)}"
                        if email is not None:
                                path += f"&email={urllib.parse.quote(email)}"
                        if name is not None:
                                path += f"&name={urllib.parse.quote(name)}"
                        if inviteCode is not None:
                                path += f"&invite={inviteCode}"
                        if threadID is not None:
                                path += f"&threadid={threadID}"
                        # Return the entered data to display in the form.
                        return redirect(path)
        else:
                return redirect(path)


def submit_post():
        if ProtocolKey.THREAD_ID not in request.form:
                abort(400)

        threadID = request.form[ProtocolKey.THREAD_ID]
        try:
                threadID = uuid.UUID(threadID)
        except ValueError:
                abort(400)
        
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)
        else:
                abort(401)

        body = request.form[ProtocolKey.POST_BODY]
        groupID = request.form[ProtocolKey.GROUP_ID]
        path = "/scape?threadid=" + str(threadID)
        response = content.post_make(userID, groupID, threadID, body, [])
        
        if response.errorCode != ContentError.OK:
                path += "&submissionerr=" + response.errorCode
        
        return redirect(path)


def submit_thread():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                user = models.User.get(userID=userID)
        else:
                abort(401)
        
        if request.method == "POST":
                attachments = []
                error = None
                groupID = request.form[ProtocolKey.GROUP_ID]
                description = request.form[ProtocolKey.THREAD_DESCRIPTION]
                title = request.form[ProtocolKey.THREAD_TITLE]

                groupType = content.group_type_get(groupID)
                if groupType == GroupType.CLIQUE:
                        response = content.clique_thread_make(userID, groupID, title, description, attachments)
                        error = response.errorCode
                else:
                        # We have to do a manual check here to make sure the user is allowed
                        # to submit to this room.
                        roomID = content.lr_room_id_get(request)
                        currentRoom = models.LivingRoom.get(roomID)
                        if roomID is None or \
                           currentRoom is None or \
                           currentRoom[ProtocolKey.ROOM_ID] != groupID:
                                # Unsupported country; they're not allowed to submit to it.
                                response = None
                                error = ContentError.FORBIDDEN
                        else:
                                response = content.lr_thread_make(userID, groupID, title, description, attachments)
                                error = response.errorCode

                if error != ContentError.OK:
                        path = f"/submit/thread?groupid={groupID}&submissionerr={str(error.value)}"
                else:
                        threadID = response.body[ProtocolKey.THREAD_ID]
                        path = f"/scape?threadid={str(threadID)}"

                return redirect(path)
        else:
                if "submissionerr" in request.args:
                        error = int(request.args.get("submissionerr"))
                else:
                        error = None

                groupID = request.args.get("groupid")
                now = datetime.now()
                submissionErrorMessage = None

                if error is not None:
                        if error == ContentError.FORBIDDEN:
                                submissionErrorMessage = "You don't have the required permission to submit to this group!"
                        elif error == ContentError.INVALID_THREAD_DESCRIPTION:
                                submissionErrorMessage = "A description can't be more than 10,000 characters long."
                        elif error == ContentError.INVALID_THREAD_TITLE:
                                submissionErrorMessage = "A title can't be more than 140 characters long."

                return render_template("pages/submit_thread.html", 
                                copyrightYear=now.year,
                                groupID=groupID,
                                ProtocolKey=ProtocolKey,
                                submissionErrorMessage=submissionErrorMessage,
                                user=user)

def tos():
        if ProtocolKey.USER_ID in session:
                sessionID = session[ProtocolKey.SESSION_ID]
                userID = session[ProtocolKey.USER_ID]
                # Check if this is a valid session.
                userSession = models.UserSession.get(sessionID)
                if userSession is None:
                        return redirect("/logout")

                # Update session details.
                IPAddress = identity.ip_address(request)
                models.UserSession.update(sessionID, IPAddress)

                user = models.User.get(userID=userID)
        else:
                user = None

        now = datetime.now()

        return render_template("pages/tos.html",
                        copyrightYear=now.year,
                        ProtocolKey=ProtocolKey,
                        user=user)