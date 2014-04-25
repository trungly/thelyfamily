from datetime import date

from flask import render_template, request, jsonify
from app.models.member import Member, Profile
from app import app, requires_login
from app.settings import SiteSettings
from werkzeug.exceptions import BadRequest


ANNOUNCE_RANGE_IN_DAYS = 14


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html', birthday_reminders=get_birthday_reminders())


@app.route('/members', methods=['GET'])
@requires_login
def members():
    members = Member.query().fetch()
    return render_template('members.html', members=members)


def get_birthday_reminders():
    reminders = {}
    profiles = Profile.query()
    for profile in profiles:
        today = date.today()
        bday = profile.birth_date
        if bday:
            delta = bday.timetuple().tm_yday - today.timetuple().tm_yday
            if today.month == bday.month and today.day == bday.day:  # can't simply use delta cuz it breaks on leap years
                reminders[profile.member.first_name] = 0
            elif 0 < delta < ANNOUNCE_RANGE_IN_DAYS:
                reminders[profile.member.first_name] = delta
    return sorted(reminders.iteritems(), key=lambda x: x[1])  # returns a list of tuples sorted by delta


@app.route('/admin', methods=['GET'])
@requires_login
def admin():
    # basic_settings_form = AdminBasicSettingsForm(request.form, **SiteSettings.as_dict())
    # return render_template('admin.html', basic_settings_form=basic_settings_form)
    return render_template('admin.html')


@app.route('/admin/settings', methods=['GET'])
@requires_login
def settings():
    return jsonify({'settings': SiteSettings.as_name_value_list()})


@app.route('/admin/settings/update', methods=['POST'])
@requires_login
def update_settings():
    SiteSettings.update(request.json['settings'])
    return '', 200
