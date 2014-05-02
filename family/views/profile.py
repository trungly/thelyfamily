from google.appengine.ext import blobstore
from werkzeug.exceptions import Unauthorized, BadRequest
from flask import g, url_for, render_template, request, flash, redirect
from family.decorators import requires_login
from family.forms import ChangePasswordForm, MemberProfileForm
from family.settings import SiteSettings
from family import app


@app.route('/profile', methods=['GET'])
@requires_login
def profile():
    form = MemberProfileForm(request.form, g.member.profile)
    return _render_profile(form)


def _render_profile(form):
    form.member_id.data = g.member.key.id()
    form.first_name.data = g.member.first_name
    form.last_name.data = g.member.last_name
    photo_upload_url = blobstore.create_upload_url(url_for('profile_photo'))
    profile_photo_url = g.member.profile.photo_url
    instagram_auth_url = 'https://instagram.com/oauth/authorize/?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code'
    instagram_auth_url = instagram_auth_url.format(
        client_id=SiteSettings.get('instagram.client.id'),
        redirect_uri='http://%s/photos/return' % SiteSettings.get('host.name'),
    )
    facebook_auth_url = 'https://www.facebook.com/dialog/oauth?client_id={app_id}&redirect_uri={redirect_uri}&scope={scope}'
    facebook_auth_url = facebook_auth_url.format(
        app_id=SiteSettings.get('facebook.lyfam.id'),
        redirect_uri='http://%s/facebook/return' % SiteSettings.get('host.name'),
        scope='user_photos'
    )

    context = {
        'form': form,
        'password_form': ChangePasswordForm(),
        'photo_upload_url': photo_upload_url,
        'profile_photo_url': profile_photo_url,
        'instagram_auth_url': instagram_auth_url,
        'facebook_auth_url': facebook_auth_url,
    }
    return render_template('profile.html', **context)


@app.route('/profile', methods=['POST'])
@requires_login
def profile_update():
    form = MemberProfileForm(request.form)

    # ensure members can only update their own profiles
    if str(form.member_id.data) != str(g.member.key.id()):
        return Unauthorized()

    if not form.validate():
        return _render_profile(form)

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


@app.route('/profile/notifications/update', methods=['POST'])
@requires_login
def update_notifications():
    if not request.is_xhr:
        return BadRequest()

    g.member.profile.update_notifications(request.form)
    return '', 200
