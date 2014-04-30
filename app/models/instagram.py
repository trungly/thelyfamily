from google.appengine.ext import ndb
from app.models import JsonSerializable


class InstagramUser(ndb.Model, JsonSerializable):
    """ Represents an Instagram user including their current access_token """

    userid = ndb.StringProperty()
    member_key = ndb.KeyProperty(kind='Member')
    access_token = ndb.StringProperty()
    # last_access_date = ndb.DateTimeProperty(auto_now_add=True)
    username = ndb.StringProperty()
    full_name = ndb.StringProperty()
    profile_picture = ndb.StringProperty()
    website = ndb.StringProperty()
    bio = ndb.StringProperty()
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
