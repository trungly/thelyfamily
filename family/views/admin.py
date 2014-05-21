from flask import render_template, jsonify, request
from family import app
from family.decorators import requires_login
from family.models.member import Member


@app.route('/admin', methods=['GET'])
@requires_login
def admin():
    return render_template('admin.html')


@app.route('/admin/settings', methods=['GET'])
@requires_login
def all_settings():
    return jsonify({'settings': app.settings.get_all(as_name_value_list=True)})


@app.route('/admin/settings/update', methods=['POST'])
@requires_login
def update_settings():
    app.settings.set_all(request.json['settings'])
    return '', 200


@app.route('/admin/settings/reset', methods=['GET'])
@requires_login
def reset_settings():
    app.settings.set('settings.initialized', False)
    from family.settings import SiteSettings
    app.settings = SiteSettings(app)
    return '', 200


@app.route('/admin/members', methods=['GET'])
@requires_login
def all_members():
    members = Member.query().fetch()
    serialized_members = [m.to_dict(exclude=['profile_key']) for m in members]
    return jsonify({'members': serialized_members})
