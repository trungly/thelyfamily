from google.appengine.ext import ndb
from family.utils import pretty_date


class ChatSubscriber(ndb.Model):
    """ This is simply a persisted list of jids, which is an XMPP chat address
    Here, we use jid as the special unique "key_name", an NDB concept that acts as a unique id for the entity
    """
    is_online = ndb.BooleanProperty()

    @classmethod
    def add_subscriber(cls, jid):
        cls.get_or_insert(jid)

    @classmethod
    def remove_subscriber(cls, jid):
        key = ndb.Key(cls, jid)
        key.delete()


class ChatMessage(ndb.Model):
    sender = ndb.StringProperty(required=True)
    body = ndb.StringProperty(required=True)
    posted_date = ndb.DateTimeProperty(auto_now_add=True)
    humanized_posted_date = ndb.ComputedProperty(lambda self: pretty_date(time=self.posted_date))

    @classmethod
    def save_message(cls, sender, body):
        message = cls(sender=sender, body=body)
        message.put()
