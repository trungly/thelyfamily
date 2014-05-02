import datetime

from google.appengine.api import images
from google.appengine.ext import ndb

from family.models import JsonSerializable
from family.models.instagram import InstagramUser
from family.models.facebook import FacebookUser
from werkzeug.security import generate_password_hash, check_password_hash


class Member(ndb.Model, JsonSerializable):
    """ Represents a user of this website """

    first_name = ndb.StringProperty(required=True)  # should be unique (as we use it for login)
    first_name_lowercase = ndb.ComputedProperty(lambda self: self.first_name.lower())  # allow case-insensitive login
    last_name = ndb.StringProperty(required=True)
    hashed_password = ndb.StringProperty(required=True)
    is_visible = ndb.BooleanProperty(default=True)  # whether this user shows up on Members page
    is_subscribed_to_chat = ndb.BooleanProperty(default=False)
    age = ndb.ComputedProperty(lambda self: self.current_age())
    message_board_visited = ndb.DateTimeProperty()
    new_messages = ndb.ComputedProperty(lambda self: self.number_new_messages())

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
        if not self.profile.birth_date:
            return ''
        return int((datetime.date.today() - self.profile.birth_date).days/365.2425)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def number_new_messages(self):
        query = ndb.gql("SELECT __key__ FROM Message WHERE posted_date > :1", self.message_board_visited)
        return query.count()


class Profile(ndb.Model, JsonSerializable):
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
    birth_date = ndb.DateProperty()
    photo_key = ndb.BlobKeyProperty()
    notify_message_posted = ndb.BooleanProperty()
    notify_birthday_reminders = ndb.BooleanProperty()

    @property
    def member(self):
        if self.member_key:
            return self.member_key.get()
        else:
            # this profile has no associated member for some reason, search all members for this profile
            import logging
            log = logging.getLogger(__name__)
            log.warning('Hmm, there appears to be an un-owned profile: id=%s' % self.key.id())
            return Member.query(Member.profile_key == self.key).get()

    @property
    def photo_url(self):
        return images.get_serving_url(str(self.photo_key)) if self.photo_key else None

    def update_notifications(self, selections):
        all_notify_flags = ['notify_message_posted', 'notify_birthday_reminders']
        for flag in all_notify_flags:
            # clear notification flags first because only selected checkbox selections get submitted here
            setattr(self, flag, False)
            if flag in selections:
                setattr(self, flag, True)
        self.put()

    @classmethod
    def create_for_member(cls, member):
        new_profile = Profile(member_key=member.key)
        new_profile.put()
        member.profile_key = new_profile.key
        member.put()
        return new_profile
