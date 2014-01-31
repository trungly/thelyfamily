import os
import requests
import datetime
import cgi

# sys.path includes 'server/lib' due to appengine_config.py
from functools import wraps
from flask import Flask, url_for, request, flash, render_template, redirect, current_app, g, session
from werkzeug.exceptions import BadRequest, Unauthorized
from google.appengine.ext import blobstore
from google.appengine.ext import ndb

from app.models import Message, InstagramUser, Member
from app.forms import MessageForm, MemberProfileForm


app = Flask(__name__.split('.')[0])

# TODO: move this configuration stuff to its own module
app.config.from_object('config.production')

settings = os.environ.get('APP_SETTINGS')
if 'localhost' in os.environ.get('SERVER_NAME'):
    app.config.from_object('config.local')

app.config['INSTAGRAM_AUTH_URL'] = 'https://instagram.com/oauth/authorize/?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code'.format(
    client_id=app.config['CLIENT_ID'],
    redirect_uri=app.config['REDIRECT_URI'],
)


@app.before_request
def add_member_to_global():
    if 'member_id' in session:
        member_key = ndb.Key(Member, session['member_id'])
        g.member = member_key.get()  # get() looks up member from database


def requires_login(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if hasattr(g, 'member') and g.member:
            return func(*args, **kwargs)
        else:
            flash('You will need to log in before you can access this website', 'warning')
            return redirect(url_for('home'))

    return decorator


@app.route('/login', methods=['POST'])
def login():
    """ Ajax only. This supports logging in via first_name and password
    """
    if not request.is_xhr:
        return BadRequest()

    member = Member.query(
        Member.first_name_lowercase == request.form['first_name'].lower()
    ).get()

    if member and member.check_password(request.form['password']):
        session['member_id'] = member.key.id()
        return '', 200

    return Unauthorized()


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('member_id')
    return redirect(url_for('home'))


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/profile', methods=['GET'])
@requires_login
def profile():
    form = MemberProfileForm(request.form, g.member.profile)
    form.member_id.data = g.member.key.id()
    form.first_name.data = g.member.first_name
    form.last_name.data = g.member.last_name
    photo_upload_url = blobstore.create_upload_url(url_for('profile_photo'))
    profile_photo_url = g.member.profile.photo_url

    return render_template('profile.html', form=form, photo_upload_url=photo_upload_url, profile_photo_url=profile_photo_url)


@app.route('/profile', methods=['POST'])
@requires_login
def profile_update():
    form = MemberProfileForm(request.form)

    # ensure members can only update their own profiles
    if str(form.member_id.data) != str(g.member.key.id()):
        return Unauthorized()

    if not form.validate():
        return render_template('profile.html', form=form)

    profile = g.member.profile_key.get()

    # update member and profile based on form values
    g.member.first_name = form.first_name.data
    g.member.last_name = form.last_name.data
    profile.primary_email = form.primary_email.data
    profile.secondary_email = form.secondary_email.data
    profile.address = form.address.data
    profile.city = form.city.data
    profile.state = form.state.data
    profile.zip = form.zip.data
    profile.mobile_phone = form.mobile_phone.data
    profile.home_phone = form.home_phone.data
    profile.work_phone = form.work_phone.data
    profile.birthday = form.birthday.data

    profile.put()
    g.member.put()
    flash('Profile updated', 'success')

    return redirect(url_for('profile'))


@app.route('/profile/photo', methods=['POST'])
@requires_login
def profile_photo():
    _, params = cgi.parse_header(request.files['profile_photo'].headers['Content-Type'])
    profile = g.member.profile_key.get()
    profile.photo_key = blobstore.BlobKey(params['blob-key'])
    profile.put()
    return redirect(url_for('profile'))


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
        ancestor_key = ndb.Key('MessageBoard', 'main')
        message = Message(parent=ancestor_key, owner_key=g.member.key, body=form.body.data, posted_date=datetime.datetime.now())
        message.put()
    return redirect(url_for('message_board'))


@app.route('/message/<message_id>', methods=['POST'])
@requires_login
def message_delete(message_id):
    ancestor_key = ndb.Key('MessageBoard', 'main')
    message = Message.get_by_id(int(message_id), parent=ancestor_key)
    if not message:
        flash('Message not found', 'danger')
    elif message.owner != g.member:
        flash('You may only delete your own message', 'danger')
    else:
        message.key.delete()
    return redirect(url_for('message_board'))


@app.route('/photos')
@requires_login
def photos():
    all_photos = []
    for instagram_user in InstagramUser.query().fetch():
        response = requests.get(instagram_user.recent_photos_url)
        if response.ok:
            current_user_photos = response.json().get('data', None)
            if current_user_photos:
                all_photos = all_photos + current_user_photos

    return render_template('photos.html', photos=all_photos)


@app.route('/photos/return')
def instagram_return():
    """ handle return from Instagram Authentication
    """
    redirect_uri = current_app.config['REDIRECT_URI']
    client_id = current_app.config['CLIENT_ID']
    client_secret = current_app.config['CLIENT_SECRET']

    code = request.args.get('code', None)
    error = request.args.get('error', None)

    if error:
        flash('There was a problem with Instagram authentication.', 'danger')
    else:
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
        user = result.get('user', None)

        if user:
            instagram_user = g.member.instagram_user
            instagram_user.populate(
                userid=user['id'],
                access_token=result['access_token'],
                username=user['username'],
                full_name=user['full_name'],
                profile_picture=user['profile_picture'],
                website=user['website'],
                bio=user['bio'],
            )
            instagram_user.put()
        else:
            flash('There was a problem with Instagram authentication. No user object found.', 'danger')

    return redirect(url_for('photos'))


@app.route('/instagram/disconnect')
def instagram_disconnect():
    g.member.instagram_user.key.delete()
    g.member.instagram_user_key = None
    g.member.put()
    return redirect(url_for('photos'))


@app.route('/members')
@requires_login
def members():
    members = Member.query().fetch()
    return render_template('members.html', members=members)


@app.route('/social')
@requires_login
def social():
    return 'Social Stream'


@app.route('/wishlists')
@requires_login
def wishlists():
    return render_template('wishlists.html')
