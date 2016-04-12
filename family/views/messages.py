import datetime

from google.appengine.api import mail
from google.appengine.ext import ndb
from flask import request, g, render_template, redirect, url_for, flash, current_app
from family import app
from family.decorators import requires_login
from family.forms import MessageForm
from family.models.member import Profile
from family.models.message import Message


SHOW_MESSAGES_TIME_DELTA = datetime.timedelta(days=90)


@app.route('/messages', methods=['GET'])
@requires_login
def messages():
    """('MessageBoard', 'main') is the parent of all messages. Thus, this puts all messages into a single entity group
    """
    form = MessageForm()
    ancestor_key = ndb.Key('MessageBoard', 'main')
    cutoff_time = datetime.datetime.now() - SHOW_MESSAGES_TIME_DELTA
    messages = Message.query(Message.posted_date > cutoff_time, ancestor=ancestor_key).order(-Message.posted_date)
    g.member.message_board_visited = datetime.datetime.now()
    g.member.put()
    return render_template('messages.html', form=form, messages=messages,
                           notify_message_posted=g.member.profile.notify_message_posted)


@app.route('/message/new', methods=['POST'])
@requires_login
def message_new():
    form = MessageForm(request.form)
    if form.validate():
        ancestor_key = ndb.Key('MessageBoard', 'main')
        message = Message(parent=ancestor_key, owner_key=g.member.key, body=form.body.data,
                          posted_date=datetime.datetime.now())
        message.put()

        # Send notification emails to everyone subscribed
        author = g.member.first_name
        posted_date = datetime.datetime.now().strftime('%A, %B %-d, %Y at %I:%M %p')
        photo_url = g.member.profile.photo_url
        if photo_url:
            image = '%s=s60' % photo_url
        else:
            image = 'http://%s/static/images/male_bust.jpg' % current_app.settings.get('host.name')
        html_body = render_template('email/new_message_posted.html', **dict(
            author=author,
            posted_date=posted_date,
            image=image,
            message_body=message.body,
        ))
        for subscriber in Profile.query(Profile.notify_message_posted == True):
            if subscriber.primary_email:
                # TODO: put a try/except here, for when mail fails
                # here is one error I got once:
                #    DeadlineExceededError: The API call mail.Send() took too long to respond and was cancelled.
                mail.send_mail(
                    '{email_from} <{email_address}>'.format(
                        email_from=current_app.settings.get('messageboard.email.from'),
                        email_address=current_app.settings.get('messageboard.email.address')
                    ),
                    subscriber.primary_email,
                    '%s posted a new message on TheLyFamily.com' % g.member.first_name,
                    '%s wrote this on %s: %s' % (author, posted_date, message.body),
                    html=html_body,
                    # reply_to='%s' % current_app.settings.get('messageboard.email.replyto')  # TODO: this should post a message on the message board
                )
    return redirect(url_for('messages'))


@app.route('/message/edit/<message_id>', methods=['POST'])
@requires_login
def message_edit(message_id):
    form = MessageForm(request.form)
    if form.validate():
        ancestor_key = ndb.Key('MessageBoard', 'main')
        message = Message.get_by_id(int(message_id), parent=ancestor_key)
        if not message:
            flash('Cannot edit. Message not found', 'danger')
        elif message.owner != g.member:
            flash('You may only edit your own message', 'danger')
        else:
            flash('Message successfully updated!', 'info')
            message.body = form.data['body']
            message.put()
        return redirect(url_for('messages'))


@app.route('/message/delete/<message_id>', methods=['POST'])
@requires_login
def message_delete(message_id):
    if request.form.get('_method', '').lower() == 'delete':
        ancestor_key = ndb.Key('MessageBoard', 'main')
        message = Message.get_by_id(int(message_id), parent=ancestor_key)
        if not message:
            flash('Message not found', 'danger')
        elif message.owner != g.member:
            flash('You may only delete your own message', 'danger')
        else:
            message.key.delete()
        return redirect(url_for('messages'))
