from google.appengine.ext import ndb
from google.appengine.api import images
from app.utils import pretty_date
from werkzeug.security import generate_password_hash, check_password_hash


class Member(ndb.Model):
    """ Represents a user of this website """

    first_name = ndb.StringProperty(required=True)  # should be unique (as we use it for login)
    first_name_lowercase = ndb.ComputedProperty(lambda self: self.first_name.lower())  # allow case-insensitive login
    last_name = ndb.StringProperty(required=True)
    hashed_password = ndb.StringProperty(required=True)

    google_user_id = ndb.StringProperty()
    facebook_user_id = ndb.StringProperty()
    instagram_user_id = ndb.StringProperty()
    profile_key = ndb.KeyProperty(kind='Profile')

    @property
    def profile(self):
        if self.profile_key:
            return self.profile_key.get()
        else:
            Profile.create_for_member(self)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Profile(ndb.Model):
    """ Represents a member's profile. There is a one to one relationship between Member and Profile """

    member_key = ndb.KeyProperty(kind=Member)
    primary_email = ndb.StringProperty()
    secondary_email = ndb.StringProperty()
    address = ndb.StringProperty()
    city = ndb.StringProperty()
    state = ndb.StringProperty()
    zip = ndb.StringProperty()
    mobile_phone = ndb.StringProperty()
    home_phone = ndb.StringProperty()
    work_phone = ndb.StringProperty()
    birthday = ndb.DateProperty()  # todo: change to birth_date
    photo_key = ndb.BlobKeyProperty()

    @property
    def member(self):
        return self.member_key.get() if self.member_key else None

    @property
    def photo_url(self):
        return images.get_serving_url(str(self.photo_key)) if self.photo_key else None

    @classmethod
    def create_for_member(cls, member):
        new_profile = Profile(member_key=member.key)
        new_profile.put()
        member.profile_key = new_profile.key
        member.put()
        return new_profile


class Message(ndb.Model):
    """ Represents a message on the message board """

    owner_key = ndb.KeyProperty(kind=Member)
    body = ndb.TextProperty()
    posted_date = ndb.DateTimeProperty()
    humanized_posted_date = ndb.ComputedProperty(lambda self: pretty_date(time=self.posted_date))

    @property
    def owner(self):
        return self.owner_key.get() if self.owner_key else None


class InstagramUser(ndb.Model):
    """ Represents an Instagram user including their current access_token """

    id = ndb.StringProperty()  # 38721310
    access_token = ndb.StringProperty()  # 38721310.2dfd347.ff2c1b40aa704711b2d9b66f869b2e12
    # last_access_date = ndb.DateTimeProperty(auto_now_add=True)
    username = ndb.StringProperty()  # trungly
    full_name = ndb.StringProperty()  # Trung  Ly
    profile_picture = ndb.StringProperty()  # http://images.ak.instagram.com/profiles/profile_38721310_75sq_1340060663.jpg
    website = ndb.StringProperty()  # http://blog.thelyfamily.com
    bio = ndb.StringProperty()  # Husband, dad, web developer enjoying the good life in Santa Monica, CA.

    @classmethod
    def from_id(cls, id=id):
        return cls.query(id=id)
