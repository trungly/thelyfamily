import os
import requests

# sys.path includes 'server/lib' due to appengine_config.py
from flask import Flask, url_for, request, flash, render_template, redirect, current_app
from google.appengine.api import users
from google.appengine.ext import ndb

from app.models import SiteMember, InstagramUser
from app.forms import SiteMemberForm


app = Flask(__name__.split('.')[0])

app.config.from_object('config.production')
settings = os.environ.get('APP_SETTINGS')
if 'localhost' in os.environ.get('SERVER_NAME'):
    app.config.from_object('config.local')


@app.route('/')
def home():
    """ Return home template at application root URL"""

    user = users.get_current_user()

    return render_template(
        'home.html',
        user=user,
        login_url=users.create_login_url(),
        logout_url=users.create_logout_url(url_for('home'))
    )


@app.route('/secure/info')
def info():
    return 'Private info'


@app.route('/myprofile', methods=['GET'])
def myprofile():
    google_user = users.get_current_user()
    site_member = SiteMember.get_by_id(str(google_user.user_id()))
    if not site_member:
        site_member = SiteMember(id=google_user.user_id())
        site_member.primary_email = google_user.email()

    form = SiteMemberForm(request.form, site_member)

    return render_template('myprofile.html', form=form)


@app.route('/myprofile/update', methods=['POST'])
@ndb.transactional
def myprofile_update():
    google_user = users.get_current_user()
    form = SiteMemberForm(request.form)
    if form.validate():
        # try to find the user
        site_member = SiteMember.get_by_id(str(google_user.user_id()))
        if not site_member:
            # if not found, create a new one based on the google_user id
            site_member = SiteMember(id=google_user.user_id())

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
        flash('Profile updated')

    return redirect(url_for('myprofile'))


@app.route('/messages')
def messages():
    return 'Message Board'


@app.route('/photos')
def photos():
    redirect_uri = current_app.config['REDIRECT_URI']
    client_id = current_app.config['CLIENT_ID']
    client_secret = current_app.config['CLIENT_SECRET']
    instagram_auth_url = current_app.config['INSTAGRAM_AUTH_URL']

    code = request.args.get('code', None)
    error = request.args.get('error', None)

    if code:
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
        print result
        if 'access_token' in result:
            # token looks like this: 38721310.2dfd347.ff2c1b40aa704711b2d9b66f869b2e12
            user = result['user']
            instagram_user = InstagramUser.query(InstagramUser.id == user['id']).get()

            if not instagram_user:
                print "No User Found"
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
                flash("Good news. You've already authenticated with Instagram!")
                print "User Found!"

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

            return render_template('photos.html', instagram_auth_url=instagram_auth_url, photos=result['data'])

    elif error:
        # Instagram error - TODO
        print error

    else:
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
            photos = result['data']
            if photos:
                all_photos = all_photos + photos
            else:
                print 'Why no photos for %s?' % get_photos_url

            return render_template('photos.html', instagram_auth_url=instagram_auth_url, photos=all_photos)

    return render_template('photos.html', instagram_auth_url=instagram_auth_url)



@app.route('/members')
def members():
    return 'Member Data'


@app.route('/logout')
def logout():
    return 'logout'


@app.route('/social')
def social():
    return 'Social Stream'


@app.route('/wishlists')
def wishlists():
    return 'Wishlists'
