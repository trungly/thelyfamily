from datetime import datetime, date, time
from json import dumps
from google.appengine.ext import ndb


class JsonSerializable(object):
    def serialized(self):
        obj = self.to_dict()
        for (k, v) in obj.iteritems():
            if isinstance(v, ndb.Key):
                obj[k] = v.id()
            elif isinstance(v, (datetime, date, time)):
                obj[k] = str(v)
        return dumps(obj)
