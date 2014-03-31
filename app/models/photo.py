import datetime
from google.appengine.ext import ndb


class Photo(ndb.Model):
    link = ndb.StringProperty()
    created_time = ndb.DateTimeProperty()
    thumbnail = ndb.StringProperty()
    source = ndb.StringProperty()
    likes_count = ndb.IntegerProperty()
    comments_count = ndb.IntegerProperty()
    caption = ndb.StringProperty()
    user_name = ndb.StringProperty()

    @classmethod
    def from_instagram_photo(cls, photo):
        return cls(
            link=photo['link'],
            created_time=datetime.datetime.fromtimestamp(int(photo['created_time'])),
            thumbnail=photo['images']['thumbnail']['url'],
            source=photo['images']['standard_resolution']['url'],
            likes_count=photo['likes']['count'],
            comments_count=photo['comments']['count'],
            caption=photo['caption']['text'] if photo['caption'] else None,
            user_name=photo['user']['full_name'],
        )

    @classmethod
    def from_facebook_photo(cls, photo):
        return cls(
            link=photo['link'],
            created_time=datetime.datetime.strptime(photo['created_time'], "%Y-%m-%dT%H:%M:%S+0000"),
            thumbnail=photo['picture'],
            source=photo['source'],
            likes_count=len(photo.get('likes', {'data': []})['data']),
            comments_count=len(photo.get('comments', {'data': []})['data']),
            caption=getattr(photo, 'name', None),
            user_name=photo['from']['name'],
        )
