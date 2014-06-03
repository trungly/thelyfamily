import cgi
import datetime
import requests

from google.appengine.ext import blobstore
from flask import current_app, request, g, redirect, url_for, flash, render_template
from family import app
from family.decorators import requires_login
from family.facebook import Facebook
from family.models.photo import Photo
from family.models.instagram import InstagramUser
from family.models.facebook import FacebookUser


@app.route('/profile/photo', methods=['POST'])
@requires_login
def profile_photo():
    _, params = cgi.parse_header(request.files['profile_photo'].headers['Content-Type'])
    profile = g.member.profile
    profile.photo_key = blobstore.BlobKey(params['blob-key'])
    profile.put()
    return redirect(url_for('profile'))


@app.route('/profile/photo/delete', methods=['POST'])
@requires_login
def profile_photo_delete():
    profile = g.member.profile
    photo_key = profile.photo_key
    blobstore.delete(photo_key)
    profile.photo_key = None
    profile.put()
    return '', 200


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
    client_id = current_app.settings.get('instagram.client.id')
    client_secret = current_app.settings.get('instagram.client.secret')

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
            'redirect_uri': 'http://%s/photos/return' % current_app.settings.get('host.name'),
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
                flash('There was a problem with verifying access_token: ' + response.json()['error']['message'],
                      'danger')
        else:
            flash('There was a problem with retrieving access_token: ' + response.content, 'danger')
    else:
        flash('There was a problem with Facebook authentication: No code.', 'danger')

    flash('Successfully connected your account!', 'success')
    return redirect('%s#connect-accounts' % url_for('profile'))
