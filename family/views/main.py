from datetime import date
from flask import render_template, request, redirect, url_for
from family.decorators import requires_login
from family.models.member import Member, Profile
from family.forms import SetupWizardForm
from family import app


ANNOUNCE_RANGE_IN_DAYS = 14


@app.route('/', methods=['GET'])
def home():
    return render_template(
        'home.html',
        settings_initialized=app.settings.initialized,
        birthday_reminders=get_birthday_reminders()
    )


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


@app.route('/admin/setup/wizard', methods=['GET', 'POST'])
def setup_wizard():
    form = SetupWizardForm(request.form)
    if request.method == 'GET':
        form.admin_first_name.data = ''
        form.admin_last_name.data = ''
        form.site_name.data = app.settings.get('site.name')
        form.secret_key.data = app.settings.get('secret.key')
        form.host_name.data = app.settings.get('host.name')
    elif request.method == 'POST' and form.validate():
        admin = Member.query(
            Member.first_name_lowercase == form.admin_first_name.data.lower()
            and
            Member.first_name_lowercase == form.admin_last_name.data.lower()
        ).get()
        if not admin:
            admin = Member(
                first_name=form.admin_first_name.data,
                last_name=form.admin_last_name.data,
                is_admin=True,
            )
            admin.set_password('admin')
            admin.put()

        app.settings.set('site.name', form.site_name.data)
        app.settings.set('secret.key', form.secret_key.data)
        app.settings.set('host.name', form.host_name.data)
        app.settings.set('settings.initialized', True)
        return redirect(url_for('home'))

    return render_template('setup_wizard.html', form=form)
