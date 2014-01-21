import os
import requests
import datetime
import cgi

# sys.path includes 'server/lib' due to appengine_config.py
from functools import wraps
from flask import Flask, url_for, request, flash, render_template, redirect, current_app, g
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb

from app.models import SiteMember, Message, InstagramUser
from app.forms import SiteMemberForm, MessageForm


app = Flask(__name__.split('.')[0])

app.config.from_object('config.production')

settings = os.environ.get('APP_SETTINGS')
if 'localhost' in os.environ.get('SERVER_NAME'):
    app.config.from_object('config.local')


@app.before_request
def add_google_user_to_global():
    g.user = users.get_current_user()
    if g.user:
        g.login_or_logout_url = users.create_logout_url(url_for('home'))
    else:
        g.login_or_logout_url = users.create_login_url(url_for('after_login'))


def requires_login(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        user = users.get_current_user()
        if not user:
            flash('You will need to log in before you can access this website', 'warning')
            return redirect(url_for('home'))
        return func(*args, **kwargs)

    return decorator


@app.route('/afterlogin')
def after_login():
    """ Create a new site user if one doesn't exist for this Google user """
    user = users.get_current_user()
    if user:
        site_member = SiteMember.get_by_id(str(g.user.user_id()))
        if not site_member:
            site_member = SiteMember(id=g.user.user_id())
            site_member.primary_email = g.user.email()
            site_member.put()
    return redirect(url_for('home'))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/myprofile', methods=['GET'])
@requires_login
def myprofile():
    site_member = SiteMember.get_by_id(str(g.user.user_id()))

    # the site member should exist at this point; but just in case...
    if not site_member:
        site_member = SiteMember(id=g.user.user_id())
        site_member.primary_email = g.user.email()

    form = SiteMemberForm(request.form, site_member)

    photo_upload_url = blobstore.create_upload_url(url_for('myprofile_photo'))

    return render_template('myprofile.html', form=form, photo_upload_url=photo_upload_url, photo_serving_url=site_member.photo_url(size=220))


@app.route('/myprofile/update', methods=['POST'])
@requires_login
def myprofile_update():
    form = SiteMemberForm(request.form)
    site_member = SiteMember.get_by_id(str(g.user.user_id()))
    if form.validate():
        site_member.first_name = form.first_name.data
        site_member.last_name = form.last_name.data
        site_member.primary_email = form.primary_email.data
        site_member.secondary_email = form.secondary_email.data
        site_member.address = form.address.data
        site_member.city = form.city.data
        site_member.state = form.state.data
        site_member.zip = form.zip.data
        site_member.mobile_phone = form.mobile_phone.data
        site_member.home_phone = form.home_phone.data
        site_member.work_phone = form.work_phone.data
        site_member.birthday = form.birthday.data

        site_member.put()
        flash('Profile updated', 'success')
    else:
        flash('There was an error saving your profile', 'danger')
        photo_upload_url = blobstore.create_upload_url(url_for('myprofile_photo'))
        return render_template('myprofile.html', form=form, photo_upload_url=photo_upload_url, photo_serving_url=site_member.photo_url(size=220))

    return redirect(url_for('myprofile'))


@app.route('/myprofile/photo', methods=['POST'])
@requires_login
def myprofile_photo():
    _, params = cgi.parse_header(request.files['profile_photo'].headers['Content-Type'])
    photo_key = blobstore.BlobKey(params['blob-key'])
    site_member = SiteMember.get_by_id(str(g.user.user_id()))
    site_member.photo_key = photo_key
    site_member.put()
    return redirect(url_for('myprofile'))


@app.route('/messages', methods=['GET'])
@requires_login
def message_board():
    form = MessageForm()
    ancestor_key = ndb.Key('MessageBoard', 'main')  # ('MessageBoard', 'main') is the parent of all messages
                                                    # Thus, this puts all messages into a single entity group
    messages = Message.query(ancestor=ancestor_key).order(-Message.posted_date)
    return render_template('message_board.html', form=form, messages=messages)


@app.route('/message/new', methods=['POST'])
@requires_login
def message_new():
    form = MessageForm(request.form)
    if form.validate():
        user_key = ndb.Key(SiteMember, g.user.user_id())
        ancestor_key = ndb.Key('MessageBoard', 'main')
        message = Message(parent=ancestor_key, owner=user_key, body=form.body.data, posted_date=datetime.datetime.now())
        message.put()
    return redirect(url_for('message_board'))


@app.route('/message/<message_id>', methods=['POST'])
@requires_login
def message_delete(message_id):
    message_key = ndb.Key('MessageBoard', 'main', Message, int(message_id))
    if g.user.user_id() == message_key.get().owner.id():
        message_key.delete()
    else:
        flash('You may only delete your own message', 'danger')
    return redirect(url_for('message_board'))


@app.route('/photos/return')
def photos_return():
    redirect_uri = current_app.config['REDIRECT_URI']
    client_id = current_app.config['CLIENT_ID']
    client_secret = current_app.config['CLIENT_SECRET']

    code = request.args.get('code', None)
    error = request.args.get('error', None)

    if error:
        print error
        flash('There was a problem with Instagram auth', 'danger')
        return redirect(url_for('home'))

    # This is case we are coming back from a successful Instagram Auth call
    url = 'https://api.instagram.com/oauth/access_token'
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': code,
    }
    response = requests.post(url, data=payload)
    result = response.json()

    if 'access_token' in result:
        # token looks like this: 38721310.2dfd347.ff2c1b40aa704711b2d9b66f869b2e12
        user = result['user']
        instagram_user = InstagramUser.query(InstagramUser.id == user['id']).get()

        if not instagram_user:
            # User doesn't exist yet; store them in the database
            instagram_user = InstagramUser(
                id=user['id'],
                access_token=result['access_token'],
                username=user['username'],
                full_name=user['full_name'],
                profile_picture=user['profile_picture'],
                website=user['website'],
                bio=user['bio'],
            )
            instagram_user.put()
        else:
            flash('Good news. You have already authenticated with Instagram!', 'info')
    else:
        flash('There was a problem with Instagram auth. No access_token found', 'danger')

    return redirect(url_for('photos'))


@app.route('/photos')
@requires_login
def photos():
    all_instagram_users = InstagramUser.query().fetch(100)  # max 100 results, just in case
    all_photos = []

    for instagram_user in all_instagram_users:
        print instagram_user
        get_photos_url = (
            'https://api.instagram.com/v1/users/{user_id}/media/recent'
            '?access_token={access_token}'
            .format(
                user_id=instagram_user.id,
                access_token=instagram_user.access_token,
            )
        )
        # print get_photos_url
        response = requests.get(get_photos_url)
        result = response.json()
        user_photos = result['data']
        if user_photos:
            all_photos = all_photos + user_photos
        else:
            print 'Why no photos for %s?' % get_photos_url

    instagram_auth_url = 'https://instagram.com/oauth/authorize/?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code'.format(
        client_id=current_app.config['CLIENT_ID'],
        redirect_uri=current_app.config['REDIRECT_URI'],
    )

    return render_template('photos.html', instagram_auth_url=instagram_auth_url, photos=all_photos)


@app.route('/members')
@requires_login
def members():
    m = SiteMember.query().fetch()
    return render_template('members.html', members=m)


@app.route('/social')
@requires_login
def social():
    return 'Social Stream'


@app.route('/wishlists')
@requires_login
def wishlists():
    return render_template('wishlists.html')
