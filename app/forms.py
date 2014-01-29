from flask_wtf import Form
from wtforms.ext.appengine.ndb import model_form
from wtforms.fields import StringField, HiddenField
from wtforms import validators

from app.models import Message, Profile


BaseProfileForm = model_form(Profile, Form, field_args={
    'birthday': {'validators': [validators.optional()]}}  # disable DateField validator
)


class MemberProfileForm(BaseProfileForm):
    member_id = HiddenField()
    first_name = StringField('First Name', [validators.input_required()])
    last_name = StringField('Last Name', [validators.input_required()])


MessageForm = model_form(Message, Form)
