from google.appengine.ext import ndb


class Setting(ndb.Model):
    name = ndb.StringProperty()
    value = ndb.GenericProperty()
