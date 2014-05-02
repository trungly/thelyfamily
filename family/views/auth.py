from google.appengine.ext import ndb
from werkzeug.exceptions import BadRequest, Unauthorized
from flask import session, g, redirect, url_for, request, jsonify
from family.forms import ChangePasswordForm
from family.models.member import Member
from family.decorators import requires_login
from family import app


@app.before_request
def add_member_to_global():
    if 'member_id' in session:
        member_key = ndb.Key(Member, session['member_id'])
        g.member = member_key.get()


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
        if request.form.get('stay_logged_in', False):
            session.permanent = True
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
