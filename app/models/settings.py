from google.appengine.ext import ndb


class Settings(ndb.Model):
    name = ndb.StringProperty()
    value = ndb.StringProperty()
