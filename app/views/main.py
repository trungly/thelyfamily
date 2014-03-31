from flask import render_template
from app.models.member import Member
from app import app, requires_login


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/members')
@requires_login
def members():
    members = Member.query().fetch()
    return render_template('members.html', members=members)
