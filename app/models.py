import datetime

from google.appengine.ext import ndb
from google.appengine.api import images
from app.utils import pretty_date
from werkzeug.security import generate_password_hash, check_password_hash
from app.facebook import Facebook


class Member(ndb.Model):
    """ Represents a user of this website """

    first_name = ndb.StringProperty(required=True)  # should be unique (as we use it for login)
    first_name_lowercase = ndb.ComputedProperty(lambda self: self.first_name.lower())  # allow case-insensitive login
    last_name = ndb.StringProperty(required=True)
    hashed_password = ndb.StringProperty(required=True)
    is_visible = ndb.BooleanProperty(default=True)  # whether this user shows up on Members page
    age = ndb.ComputedProperty(lambda self: self.current_age())

    profile_key = ndb.KeyProperty(kind='Profile')
    google_user_key = ndb.KeyProperty(kind='GoogleUser')
    facebook_user_key = ndb.KeyProperty(kind='FacebookUser')
    instagram_user_key = ndb.KeyProperty(kind='InstagramUser')

    @property
    def profile(self):
        if self.profile_key:
            return self.profile_key.get()
        else:
            return Profile.create_for_member(self)

    @property
    def instagram_user(self):
        if self.instagram_user_key:
            return self.instagram_user_key.get()
        else:
            return InstagramUser.create_for_member(self)

    @property
    def facebook_user(self):
        if self.facebook_user_key:
            return self.facebook_user_key.get()
        else:
            return FacebookUser.create_for_member(self)

    def current_age(self):
        if not self.profile.birthday:
            return ''
        return int((datetime.date.today() - self.profile.birthday).days/365.2425)

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

    userid = ndb.StringProperty()  # 38721310
    member_key = ndb.KeyProperty(kind=Member)
    access_token = ndb.StringProperty()  # 38721310.2dfd347.ff2c1b40aa704711b2d9b66f869b2e12
    # last_access_date = ndb.DateTimeProperty(auto_now_add=True)
    username = ndb.StringProperty()  # trungly
    full_name = ndb.StringProperty()  # Trung Ly
    profile_picture = ndb.StringProperty()  # http://images.ak.instagram.com/profiles/profile_38721310_75sq_1340060663.jpg
    website = ndb.StringProperty()  # http://blog.thelyfamily.com
    bio = ndb.StringProperty()  # Husband, dad, web developer enjoying the good life in Santa Monica, CA.
    recent_photos_url = ndb.ComputedProperty(
        lambda self: 'https://api.instagram.com/v1/users/{user_id}/media/recent?access_token={access_token}'
        .format(
            user_id=self.userid,
            access_token=self.access_token,
        )
    )

    @classmethod
    def create_for_member(cls, member):
        new_instagram_user = InstagramUser(member_key=member.key)
        new_instagram_user.put()
        member.instagram_user_key = new_instagram_user.key
        member.put()
        return new_instagram_user


class FacebookUser(ndb.Model):
    """ Represents a Facebook user
    """
    member_key = ndb.KeyProperty(kind=Member)
    userid = ndb.IntegerProperty()
    access_token = ndb.StringProperty()
    expires_at = ndb.DateTimeProperty()
    scopes = ndb.JsonProperty()
    recent_photos_url = ndb.ComputedProperty(Facebook.uploaded_photos_url)

    @classmethod
    def create_for_member(cls, member):
        new_facebook_user = FacebookUser(member_key=member.key)
        new_facebook_user.put()
        member.facebook_user_key = new_facebook_user.key
        member.put()
        return new_facebook_user


class Photo(ndb.Model):
    link = ndb.StringProperty()
    created_time = ndb.DateTimeProperty()
    thumbnail = ndb.StringProperty()
    source = ndb.StringProperty()
    likes_count = ndb.IntegerProperty()
    comments_count = ndb.IntegerProperty()
    caption = ndb.StringProperty()
    user_name = ndb.StringProperty()

    @classmethod
    def from_instagram_photo(cls, photo):
        return cls(
            link=photo['link'],
            created_time=datetime.datetime.fromtimestamp(int(photo['created_time'])),
            thumbnail=photo['images']['thumbnail']['url'],
            source=photo['images']['standard_resolution']['url'],
            likes_count=photo['likes']['count'],
            comments_count=photo['comments']['count'],
            caption=photo['caption']['text'] if photo['caption'] else None,
            user_name=photo['user']['full_name'],
        )

    @classmethod
    def from_facebook_photo(cls, photo):
        return cls(
            link=photo['link'],
            created_time=datetime.datetime.strptime(photo['created_time'], "%Y-%m-%dT%H:%M:%S+0000"),
            thumbnail=photo['picture'],
            source=photo['source'],
            likes_count=len(photo.get('likes', {'data': []})['data']),
            comments_count=len(photo.get('comments', {'data': []})['data']),
            caption=getattr(photo, 'name', None),
            user_name=photo['from']['name'],
        )
