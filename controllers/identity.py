import os
import re
import uuid
from datetime import datetime, timedelta

import geoip2.database
from flask_mail import Message

from app import APP_ROOT, config, mail, models
from app.constants import LoginStatus, ProtocolKey, SignupStatus, UserError
from controllers import content, presence
from controllers.crypto import sha256_str

reservedAliases = {"admin", "api", "cliques", "comment", "connections", "error", "forgot", "home", "index", "join",
                   "login", "logout", "lr", "me", "messages", "mod", "networks", "notifications", "passwordreset", "thread",
                   "post", "prefs", "profile", "requests", "signup", "submit", "user"}


def alias_exists(alias):
        user = models.User.get(alias=alias)
        if user is not None:
                return True
        else:
                return False


def creds_verify(alias, password, passwordSalted, salt):
        if alias is None:
                raise ValueError("identity.creds_verify(4): alias argument is null")
        elif password is None:
                raise ValueError("identity.creds_verify(4): password argument is null")
                
        password_salted = sha256_str(password + salt)
        if password_salted == passwordSalted:
                return True
        else:
                return False


def iso_code(IPAddress):
        if IPAddress is None:
                raise ValueError("identity.iso_code(1): IPAddress argument is null")
        
        geoDBPath = os.path.join(APP_ROOT, "db", "GeoLite2-Country.mmdb")
        reader = geoip2.database.Reader(geoDBPath)
        try:
                response = reader.country(IPAddress)
                reader.close()
                ISOCode = response.country.iso_code
        except:
                reader.close()
                ISOCode = None

        return ISOCode


# This function should be called within the context of a Flask request.
def ip_address(request):
        if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
                userIPAddress = request.environ["REMOTE_ADDR"]
        else:
                userIPAddress = request.remote_addr

        return userIPAddress


def login(alias, password):
        if alias is None:
                return LoginStatus.ERR_INVALID_ALIAS
        elif password is None:
                return LoginStatus.ERR_INVALID_PASSWORD
        
        alias = alias.strip()

        if len(alias) < 2 or len(alias) > 64:
                return LoginStatus.ERR_INVALID_ALIAS
        elif len(password) < 8 or len(password) > 64:
                return LoginStatus.ERR_INVALID_PASSWORD
        elif re.match(r"^(?!.*[-.]$)[-\w\.]+$", alias) is None:
                return LoginStatus.ERR_INVALID_ALIAS
        # A password is supposed to be a SHA256 hash.
        elif re.match(r"^[A-Fa-f0-9]{64}$", password) is None:
                return LoginStatus.ERR_INVALID_PASSWORD

        user = models.User.get(alias=alias)
        if user is None:
                return LoginStatus.ERR_NOTFOUND

        check = creds_verify(alias, password, user["password"], user["salt"])
        if check == True:
                # Check if this account has been suspended.
                if user[ProtocolKey.SUSPENDED] == 1:
                        return LoginStatus.ERR_SUSPENDED
                else:
                        return LoginStatus.OK
        elif check == False:
                return LoginStatus.ERR_CREDENTIALS
        else:
                return check

def is_valid_alias(alias):
        if re.match(r"^(?!.*[-.]$)[-\w\.]+$", alias) is None:
                return False
        else:
                return True


def is_valid_password(password):
        # A password is supposed to be a SHA256 hash.
        if re.match(r"^[A-Fa-f0-9]{64}$", password) is None:
                return False
        else:
                return True


def password_reset(userID, password, secret):
        user = models.User.get(userID=userID)
        if user is None:
                return UserError.NOT_FOUND

        if secret is None:
                return UserError.BAD_REQUEST

        if password is None:
                return UserError.ERR_INVALID_PASSWORD

        if len(password) < 8 or \
           len(password) > 64 or \
           not is_valid_password(password):
                return UserError.ERR_INVALID_PASSWORD
        
        now = datetime.now()
        resetData = models.UserPasswordReset.get(secret=secret)
        
        if resetData is not None and \
           resetData[ProtocolKey.USER_ID] == userID and \
           resetData[ProtocolKey.SECRET] == secret:
                if now-timedelta(hours=1) <= resetData[ProtocolKey.TIMESTAMP] <= now:
                        models.UserPasswordReset.delete(userID)
                        salt = uuid.uuid4().hex
                        salt = salt[:16]
                        password_salted = sha256_str(password + salt)
                        models.User.password_update(userID, password_salted, salt)

                        return UserError.OK
                else:
                        # More than an hour old (expired).
                        models.UserPasswordReset.delete(userID)
                        return UserError.EXPIRED_LINK
        else:
                return UserError.BAD_REQUEST


def password_reset_send_email(alias, email):
        if alias is None:
                return UserError.ERR_INVALID_ALIAS
        elif email is None:
                return UserError.ERR_INVALID_EMAIL

        alias = alias.strip()
        email = email.strip()

        if len(alias) < 2 or \
           len(alias) > 64 or \
           not is_valid_alias(alias):
                return UserError.ERR_INVALID_ALIAS
        if len(email) == 0 or \
           len(email) > 120 or \
          not content.is_valid_email(email):
                return UserError.ERR_INVALID_EMAIL
        
        user = models.User.get(alias=alias)
        if user is None:
                return UserError.NOT_FOUND
        
        if user[ProtocolKey.EMAIL_ADDRESS] != email:
                return UserError.NOT_FOUND
        
        userID = user[ProtocolKey.USER_ID]
        exists = models.UserPasswordReset.get(userID=userID)
        if exists is not None:
                now = datetime.now()
                if now-timedelta(hours=1) <= exists[ProtocolKey.TIMESTAMP] <= now:
                        # Less than an hour old; reuse.
                        secret = exists[ProtocolKey.SECRET]
                else:
                        # More than an hour old (expired); generate a fresh one.
                        models.UserPasswordReset.delete(userID)
                        secret = session_id_generate()
                        models.UserPasswordReset.make(userID, secret)
        else:
                secret = session_id_generate()
                models.UserPasswordReset.make(userID, secret)

        reset_url = f"{config.APP_SCHEME}://{config.APP_DOMAIN}/forgot?passwordid={secret}"
        msg = Message("Reset your password",
                     sender=config.MAIL_DEFAULT_SENDER, 
                     recipients=[email])
        msg.body = f'''Hi!\n\nIf you recently requested to have your Cliques password reset, follow this link and enter your new password of choice: {reset_url}\n\nIf you did not initiate this reset, kindly ignore this email.\n\nThis is an automated message. Please don't reply to it.'''
        mail.send(msg)

        return UserError.OK


def profile_update(alias=None, email=None, name=None, password=None):
        print("TODO: profile_update(4)")


def session_id_generate():
        sessionID = uuid.uuid4().hex
        # Turn it into a SHA2 hash.
        return sha256_str(sessionID)


def signup(alias, email, name, password):
        if alias is None:
                return SignupStatus.ERR_INVALID_ALIAS
        elif password is None:
                return SignupStatus.ERR_INVALID_PASSWORD

        alias = alias.strip()
        
        if len(alias) < 2 or \
           len(alias) > 64 or \
           not is_valid_alias(alias):
                return SignupStatus.ERR_INVALID_ALIAS
        elif len(password) < 8 or \
             len(password) > 64 or \
             not is_valid_password(password):
                return SignupStatus.ERR_INVALID_PASSWORD
        elif alias_exists(alias):
                return SignupStatus.ERR_EXISTS

        if alias.lower() in reservedAliases:
                return SignupStatus.ERR_EXISTS

        if email is not None:
                # Sanitisation
                email = email.strip()
                if len(email) == 0 or \
                   len(email) > 120 or \
                   not content.is_valid_email(email):
                        return SignupStatus.ERR_INVALID_EMAIL

        if name is not None:
                # Sanitisation
                name = name.strip()
                if len(name) == 0 or len(name) > 64:
                        return SignupStatus.ERR_INVALID_NAME

        salt = uuid.uuid4().hex
        salt = salt[:16]
        password_salted = sha256_str(password + salt)
        userID = models.User.make(alias=alias, email=email, name=name, password=password_salted, salt=salt)
        presence.record_make(userID)
        
        return SignupStatus.OK
