from markdown2 import markdown
from google.appengine.ext import ndb
from family.models.member import Member
from family.utils import pretty_date


class Message(ndb.Model):
    """ Represents a message on the message board """

    owner_key = ndb.KeyProperty(kind=Member)
    body = ndb.TextProperty()
    posted_date = ndb.DateTimeProperty()
    humanized_posted_date = ndb.ComputedProperty(lambda self: pretty_date(time=self.posted_date))

    @property
    def owner(self):
        return self.owner_key.get() if self.owner_key else None

    @property
    def body_formatted(self):
        return markdown(self.body)
