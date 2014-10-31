from google.appengine.ext import ndb


class WishlistItem(ndb.Model):
    """ Represents an item on a user's wish list """

    name = ndb.StringProperty(required=True)
    link = ndb.StringProperty()
    details = ndb.StringProperty()
    is_giver_anonymous = ndb.BooleanProperty(default=True)
    status = ndb.StringProperty(required=True, default='open')
    created_date = ndb.DateTimeProperty()

    owner_key = ndb.KeyProperty(kind='Member')
    giver_key = ndb.KeyProperty(kind='Member')

    @property
    def giver(self):
        return self.giver_key.get() if self.giver_key else None

    def update_status(self, status, member_key):
        self.status = status
        if status == 'open':
            self.giver_key = None  # clear it out if it's open
        elif status == 'reserved' or status == 'locked':
            self.giver_key = member_key
        self.put()
