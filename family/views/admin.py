from flask import render_template, jsonify, request
from family import app
from family.decorators import requires_login
from family.settings import SiteSettings
from family.models.member import Member


@app.route('/admin', methods=['GET'])
@requires_login
def admin():
    members = Member.query().fetch()
    serialized_members = [m.serialized() for m in members]
    return render_template('admin.html', members_bootstrap_string='[%s]' % ','.join(serialized_members))


@app.route('/admin/settings', methods=['GET'])
@requires_login
def settings():
    return jsonify({'settings': SiteSettings.as_name_value_list()})


@app.route('/admin/settings/update', methods=['POST'])
@requires_login
def update_settings():
    SiteSettings.update(request.json['settings'])
    return '', 200
