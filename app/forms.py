from flask_wtf import Form
from wtforms.ext.appengine.ndb import model_form
from app.models import SiteMember, Message

SiteMemberForm = model_form(SiteMember, Form)

MessageForm = model_form(Message, Form)
