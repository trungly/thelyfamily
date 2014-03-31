from google.appengine.ext import ndb
from app.models.member import Member
from app.utils import pretty_date
from markdown2 import markdown


class Message(ndb.Model):
    """ Represents a message on the message board """

    owner_key = ndb.KeyProperty(kind=Member)
    body = ndb.TextProperty()
    body_formatted = ndb.ComputedProperty(lambda self: markdown(self.body))
    posted_date = ndb.DateTimeProperty()
    humanized_posted_date = ndb.ComputedProperty(lambda self: pretty_date(time=self.posted_date))

    @property
    def owner(self):
        return self.owner_key.get() if self.owner_key else None
