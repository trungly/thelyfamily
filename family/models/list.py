from markdown2 import markdown
from google.appengine.ext import ndb
from family.models.member import Member
from family.utils import pretty_date


class Item(ndb.Model):
    """ Represents an item on a list """

    name = ndb.TextProperty()


class List(ndb.Model):
    """ Represents a list that contains items """

    name = ndb.TextProperty()
    items = ndb.StructuredProperty(Item, repeated=True)
