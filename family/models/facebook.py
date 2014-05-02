from google.appengine.ext import ndb
from family.facebook import Facebook


class FacebookUser(ndb.Model):
    """ Represents a Facebook user
    """
    member_key = ndb.KeyProperty(kind='Member')
    userid = ndb.IntegerProperty()
    access_token = ndb.StringProperty()
    expires_at = ndb.DateTimeProperty()
    scopes = ndb.JsonProperty()
    recent_photos_url = ndb.ComputedProperty(Facebook.uploaded_photos_url)

    @classmethod
    def create_for_member(cls, member):
        new_facebook_user = cls(member_key=member.key)
        new_facebook_user.put()
        member.facebook_user_key = new_facebook_user.key
        member.put()
        return new_facebook_user
