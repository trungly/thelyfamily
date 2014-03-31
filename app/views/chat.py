import datetime

from google.appengine.api import xmpp
from google.appengine.ext import ndb

from app.models.chat import ChatSubscriber, ChatMessage
from flask import request, render_template, jsonify, g
from app import app, requires_login
from werkzeug.exceptions import NotFound


"""
TODO:
Consider sending a (self) presence message to all chat subscribers when the app starts up, and
on a shutdown hook, send a presence of unavailable
"""


@app.route('/_ah/xmpp/presence/available/', methods=['POST'])
def xmpp_subscriber_available():
    """ Called when a user comes online
    """
    from_address = request.form.get('from')
    key = ndb.Key(ChatSubscriber, from_address)
    subscriber = key.get()
    if subscriber:
        subscriber.is_online = True
        subscriber.put()
        return '', 200
    return NotFound()


@app.route('/_ah/xmpp/presence/unavailable/', methods=['POST'])
def xmpp_subscriber_unavailable():
    """ Called when a user goes offline
    """
    from_address = request.form.get('from')
    key = ndb.Key(ChatSubscriber, from_address)
    subscriber = key.get()
    if subscriber:
        subscriber.is_online = False
        subscriber.put()
        return '', 200
    return NotFound()


@app.route('/_ah/xmpp/presence/probe/', methods=['POST'])
def xmpp_subscriber_probe():
    """ Called when someone requests to see if the main website chat user is online
    """
    return '', 200


# 1) Member visits the chat page
@app.route('/chat', methods=['GET'])
@requires_login
def chat():
    # 1a) Request online status of each subscriber
    for subscriber in ChatSubscriber.query():
        xmpp.send_presence(subscriber, presence_type=xmpp.PRESENCE_TYPE_PROBE)
    return render_template('chat.html')


# 2) Asynchronously request all chat messages
@app.route('/chat/messages', methods=['GET'])
@requires_login
def chat_messages():
    cutoff = datetime.datetime.now() - datetime.timedelta(weeks=4)
    results = ChatMessage.query(ChatMessage.posted_date > cutoff).order(ChatMessage.posted_date)
    messages = [{'sender': m.sender, 'body': m.body, 'date': m.humanized_posted_date} for m in results]
    return jsonify({'messages': messages})


# 3) Asynchronously request all subscribers (including their online status)
@app.route('/chat/subscribers', methods=['GET'])
@requires_login
def chat_subscribers():
    subscribers = [{'name': s.key.id(), 'status': 'online' if s.is_online else 'offline'}
                   for s in ChatSubscriber.query()]
    return jsonify({'subscribers': subscribers})


# 4) Member clicks a link to send a chat invitation out to himself
@app.route('/chat/invite', methods=['GET'])
@requires_login
def send_invite():
    # 4a) The chat service sends an invite to the XMPP user
    xmpp.send_invite(request.args['to'])
    return '', 200


# 5) A site member posts a message to the chat server
@app.route('/_ah/xmpp/subscription/subscribed/', methods=['POST'])
def xmpp_subscribed():
    # 5a) We add him to the list of chat subscribers
    jid = request.form['from'].split('/')[0]
    ChatSubscriber.add_subscriber(jid)
    return '', 200


# 6) This is called when the user accepts the invite using his XMPP (Gtalk) chat client
@app.route('/chat/send', methods=['POST'])
@requires_login
def chat_send():
    # 5a) We only send the message to the main site XMPP user
    from_jid = '%s@the-ly-family.appspotchat.com' % g.member.first_name
    message = request.json['message']
    if message:
        xmpp.send_message('the-lyfamily@appspot.com', message, from_jid=from_jid)
    return '', 200


# 7) This is called when the message is received by the site XMPP user
@app.route('/_ah/xmpp/message/chat/', methods=['POST'])
def xmpp_receive_message():
    message = xmpp.Message(request.form)

    # 6a) Write the message to the database
    ChatMessage.save_message(message.sender, message.body)

    # 6b) Broadcast the message to all chat subscribers
    for subscriber in ChatSubscriber.query():
        xmpp.send_message(subscriber.key.id(), message)
    return '', 200


# 8) The user decides to unsubscribe from the chat
@app.route('/chat/remove', methods=['POST'])
@requires_login
def chat_remove():
    jid = request.form['subscriber']
    ChatSubscriber.remove_subscriber(jid)
    return '', 200
