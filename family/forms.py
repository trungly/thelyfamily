from flask_wtf import Form
from wtforms.ext.appengine.ndb import model_form
from wtforms.fields import StringField, HiddenField, PasswordField
from wtforms import validators
from family.models.member import Profile
from family.models.message import Message


BaseProfileForm = model_form(Profile, Form, field_args={
    'birth_date': {'validators': [validators.optional()]}}  # disable DateField validator
)


class MemberProfileForm(BaseProfileForm):
    member_id = HiddenField()
    first_name = StringField('First Name', [validators.input_required()])
    last_name = StringField('Last Name', [validators.input_required()])


class ChangePasswordForm(Form):
    old_password = PasswordField('Old Password', [validators.input_required()])
    new_password = PasswordField('New Password', [
        validators.input_required(),
        validators.equal_to('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Re-type New Password', [
        validators.input_required(),
        validators.equal_to('new_password', message='Passwords must match')
    ])


MessageForm = model_form(Message, Form)


class SetupWizardForm(Form):
    admin_first_name = StringField('Admin first name', [validators.input_required()])
    admin_last_name = StringField('Admin last name', [validators.input_required()])
    site_name = StringField('Site name', [validators.input_required()])
    secret_key = StringField('Secret key', [validators.input_required()])
    host_name = StringField('Website address', [validators.input_required()])
