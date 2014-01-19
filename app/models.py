from google.appengine.ext import ndb
from app.utils import pretty_date


class SiteMember(ndb.Model):
    """ Represents a thelyfamily.com member """

    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    primary_email = ndb.StringProperty()
    secondary_email = ndb.StringProperty()
    address = ndb.StringProperty()
    city = ndb.StringProperty()
    state = ndb.StringProperty()
    zip = ndb.StringProperty()
    mobile_phone = ndb.StringProperty()
    home_phone = ndb.StringProperty()
    work_phone = ndb.StringProperty()
    birthday = ndb.DateProperty()


class Message(ndb.Model):
    """ Represents a message on the message board """

    owner = ndb.KeyProperty()
    body = ndb.TextProperty()
    posted_date = ndb.DateTimeProperty()
    humanized_posted_date = ndb.ComputedProperty(lambda self: pretty_date(time=self.posted_date))


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

    ### An example from docs:
    # @classmethod
    # def query_book(cls, ancestor_key):
    #     return cls.query(ancestor=ancestor_key).order(-cls.date)
    @classmethod
    def from_id(cls, id=id):
        return cls.query(id=id)
