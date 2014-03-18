import requests
import datetime
import cgi

# sys.path includes 'server/lib' due to appengine_config.py
from functools import wraps
from flask import Flask, url_for, request, flash, render_template, redirect, current_app, g, session, jsonify
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.api import xmpp

from app.models import Member, Message, InstagramUser, FacebookUser, Photo, ChatSubscriber, ChatMessage
from app.forms import MessageForm, MemberProfileForm, ChangePasswordForm
from app.facebook import Facebook
from config import configure_app


app = Flask(__name__.split('.')[0])

configure_app(app)


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


@app.route('/password/change', methods=['POST'])
@requires_login
def change_password():
    if not request.is_xhr:
        return BadRequest()

    password_form = ChangePasswordForm(request.form)
    if not password_form.validate():
        r = jsonify(password_form.errors)
        return r, 400

    if not g.member.check_password(password_form.old_password.data):
        return '', 401

    g.member.set_password(request.form['new_password'])
    g.member.put()
    return '', 200


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
    password_form = ChangePasswordForm()

    return render_template('profile.html', form=form, password_form=password_form, photo_upload_url=photo_upload_url, profile_photo_url=profile_photo_url)


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
    profile.birth_date = form.birth_date.data

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
def messages():
    form = MessageForm()
    ancestor_key = ndb.Key('MessageBoard', 'main')  # ('MessageBoard', 'main') is the parent of all messages
                                                    # Thus, this puts all messages into a single entity group
    messages = Message.query(ancestor=ancestor_key).order(-Message.posted_date)
    return render_template('messages.html', form=form, messages=messages)


@app.route('/message/new', methods=['POST'])
@requires_login
def message_new():
    form = MessageForm(request.form)
    if form.validate():
        ancestor_key = ndb.Key('MessageBoard', 'main')
        message = Message(parent=ancestor_key, owner_key=g.member.key, body=form.body.data, posted_date=datetime.datetime.now())
        message.put()
    return redirect(url_for('messages'))


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
    return redirect(url_for('messages'))


@app.route('/photos')
@requires_login
def photos():
    all_photos = []
    for user in (InstagramUser.query().fetch()):
        response = requests.get(user.recent_photos_url)
        if response.ok:
            current_user_photos = response.json().get('data', None)
            current_user_photos = [Photo.from_instagram_photo(p) for p in current_user_photos]
            if current_user_photos:
                all_photos = all_photos + current_user_photos

    for user in (FacebookUser.query().fetch()):
        response = requests.get(user.recent_photos_url)
        if response.ok:
            current_user_photos = response.json().get('data', None)
            current_user_photos = [Photo.from_facebook_photo(p) for p in current_user_photos]
            if current_user_photos:
                all_photos = all_photos + current_user_photos

    return render_template('photos.html', photos=sorted(all_photos, key=lambda x: x.created_time, reverse=True))


@app.route('/photos/return')
def instagram_return():
    """ handle return from Instagram Authentication
    """
    client_id = current_app.config['INSTAGRAM_CLIENT_ID']
    client_secret = current_app.config['INSTAGRAM_CLIENT_SECRET']

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
            'redirect_uri': 'http://%s/photos/return' % current_app.config['HOST_NAME'],
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
    if g.member.instagram_user_key:
        g.member.instagram_user_key.delete()
        g.member.instagram_user_key = None
        g.member.put()
        flash('Successfully disconnected your Instagram account', 'success')
    return redirect(url_for('profile', _anchor="connect-accounts"))


@app.route('/facebook/disconnect')
def facebook_disconnect():
    if g.member.facebook_user_key:
        g.member.facebook_user_key.delete()
        g.member.facebook_user_key = None
        g.member.put()
        flash('Successfully disconnected your Facebook account', 'success')
    return redirect(url_for('profile', _anchor="connect-accounts"))


@app.route('/facebook/return')
def facebook_return():
    code = request.args.get('code', None)
    if code:
        url = Facebook.access_token_url(code)
        response = requests.get(url)
        if response.ok:
            access_token = response.content.split('&')[0].split('=')[1]
            url = Facebook.debug_token_url(access_token)

            response = requests.get(url)
            if response.ok:
                data = response.json()['data']
                facebook_user = g.member.facebook_user
                facebook_user.populate(
                    userid=data['user_id'],
                    access_token=access_token,
                    expires_at=datetime.datetime.fromtimestamp(data['expires_at']),
                    scopes=data['scopes'],
                )
                facebook_user.put()
            else:
                flash('There was a problem with verifying access_token: ' + response.json()['error']['message'], 'danger')
        else:
            flash('There was a problem with retrieving access_token: ' + response.content, 'danger')
    else:
        flash('There was a problem with Facebook authentication: No code.', 'danger')

    flash('Successfully connected your account!', 'success')
    return redirect('%s#connect-accounts' % url_for('profile'))


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


###############
# Chat Stuffs #
###############

#### Consider sending a (self) presence message to all chat subscribers when the app starts up, and
####   on a shutdown hook, send a presence of unavailable

######################## Begin Chat Status

@app.route('/_ah/xmpp/presence/available/', methods=['POST'])
def xmpp_subscriber_available():
    """ Called when a user comes online
    """
    from_address = request.form.get('from')
    key = ndb.Key(ChatSubscriber, from_address)
    subscriber = key.get()
    if subscriber:
        subscriber.is_online = True
        subscriber.put()
        return '', 200
    return NotFound()


@app.route('/_ah/xmpp/presence/unavailable/', methods=['POST'])
def xmpp_subscriber_unavailable():
    """ Called when a user goes offline
    """
    from_address = request.form.get('from')
    key = ndb.Key(ChatSubscriber, from_address)
    subscriber = key.get()
    if subscriber:
        subscriber.is_online = False
        subscriber.put()
        return '', 200
    return NotFound()


@app.route('/_ah/xmpp/presence/probe/', methods=['POST'])
def xmpp_subscriber_probe():
    """ Called when someone requests to see if the main website chat user is online
    """
    return '', 200

######################## End Chat Status


# 1) Member visits the chat page
@app.route('/chat', methods=['GET'])
@requires_login
def chat():
    # 1a) Request online status of each subscriber
    for subscriber in ChatSubscriber.query():
        xmpp.send_presence(subscriber, presence_type=xmpp.PRESENCE_TYPE_PROBE)
    return render_template('chat.html')


# 2) Asynchronously request all chat messages
@app.route('/chat/messages', methods=['GET'])
@requires_login
def chat_messages():
    cutoff = datetime.datetime.now() - datetime.timedelta(weeks=4)
    results = ChatMessage.query(ChatMessage.posted_date > cutoff).order(ChatMessage.posted_date)
    messages = [{'sender': m.sender, 'body': m.body, 'date': m.humanized_posted_date} for m in results]
    return jsonify({'messages': messages})


# 3) Asynchronously request all subscribers (including their online status)
@app.route('/chat/subscribers', methods=['GET'])
@requires_login
def chat_subscribers():
    subscribers = [{'name': s.key.id(), 'status': 'online' if s.is_online else 'offline'}
                   for s in ChatSubscriber.query()]
    return jsonify({'subscribers': subscribers})


# 4) Member clicks a link to send a chat invitation out to himself
@app.route('/chat/invite', methods=['GET'])
@requires_login
def send_invite():
    # 4a) The chat service sends an invite to the XMPP user
    xmpp.send_invite(request.args['to'])
    return '', 200


# 5) This is called when the user accepts the invite using his XMPP (Gtalk) chat client
@app.route('/_ah/xmpp/subscription/subscribed/', methods=['POST'])
def xmpp_subscribed():
    # 5a) We add him to the list of chat subscribers
    jid = request.form['from'].split('/')[0]
    ChatSubscriber.add_subscriber(jid)
    return '', 200


# 5) A site member posts a message to the chat server
@app.route('/chat/send', methods=['POST'])
@requires_login
def chat_send():
    # 5a) We only send the message to the main site XMPP user
    from_jid = '%s@the-ly-family.appspotchat.com' % g.member.first_name
    message = request.json['message']
    if message:
        xmpp.send_message('the-lyfamily@appspot.com', message, from_jid=from_jid)
    return '', 200


# 6) This is called when the message is received by the site XMPP user
@app.route('/_ah/xmpp/message/chat/', methods=['POST'])
def xmpp_receive_message():
    message = xmpp.Message(request.form)

    # 6a) Write the message to the database
    ChatMessage.save_message(message.sender, message.body)

    # 6b) Broadcast the message to all chat subscribers
    for subscriber in ChatSubscriber.query():
        xmpp.send_message(subscriber.key.id(), message)
    return '', 200


# 7) The user decides to unsubscribe from the chat
@app.route('/chat/remove', methods=['POST'])
@requires_login
def chat_remove():
    jid = request.form['subscriber']
    ChatSubscriber.remove_subscriber(jid)
    return '', 200
