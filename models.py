import hashlib
import hmac
import uuid
from google.appengine.ext import ndb

class Task(ndb.Model):
    name = ndb.StringProperty()
    message = ndb.TextProperty()
    message2 = ndb.TextProperty()
    checked = ndb.BooleanProperty(default=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    deleted = ndb.BooleanProperty(default=False)

class User(ndb.Model):
    reg_name = ndb.StringProperty();
    reg_surname = ndb.StringProperty();
    reg_email = ndb.StringProperty();
    encrypted_password = ndb.StringProperty();

    @classmethod
    def create(cls, reg_name, reg_surname, reg_email, orig_password):
        user = cls(reg_name=reg_name, reg_surname=reg_surname, reg_email=reg_email,
                   encrypted_password=cls.encrypt_password(orig_password=orig_password))
        user.put()
        return user

    @classmethod
    def encrypt_password(cls, orig_password):
        salt = uuid.uuid4().hex
        code = hmac.new(str(salt), str(orig_password), hashlib.sha512).hexdigest()
        return "%s:%s" % (code, salt)

    @classmethod
    def verify_pass(cls, orig_password, user):
        code, salt = user.encrypted_password.split(":")
        to_verify = hmac.new(str(salt), str(orig_password), hashlib.sha512).hexdigest()

        if to_verify == code:
            return True
        else:
            return False
