from flask import g, render_template, jsonify, request
from family.decorators import requires_login
from family import app
from family.models.wishlist import WishlistItem
from werkzeug.exceptions import BadRequest
from google.appengine.ext import ndb


@app.route('/wishlists')
@requires_login
def wishlists():
    return render_template('wishlists.html')

@app.route('/wishlist', methods=['GET'])
@requires_login
def get_current_user_wishlist():
    results = WishlistItem.query(WishlistItem.owner_key == g.member.key).fetch()
    return jsonify({'items': results})

@app.route('/wishlist', methods=['POST'])
@requires_login
def add_wishlist_item():
    item = WishlistItem(owner_key=g.member.key, **request.json)
    item.put()
    return '', 200

@app.route('/wishlist/<int:id>', methods=['GET'])
@requires_login
def get_member_wishlist(id):
    key = ndb.Key('Member', id)
    wishlist_items = WishlistItem.query(WishlistItem.owner_key == key).fetch()
    serialized_items = []
    for item in wishlist_items:
        # append a giver (member) dict to each wishlist item
        giver = item.giver
        item_dict = item.to_dict()
        item_dict['giver'] = giver.to_dict() if giver else None
        item_dict['id'] = item.key.id()
        serialized_items.append(item_dict)
    is_current_member_wishlist = key == g.member.key
    wishlist_title = 'My wishlist' if is_current_member_wishlist else 'This is %s\'s wishlist' % key.get().first_name
    return jsonify({'items': serialized_items, 'wishlist_title': wishlist_title, 'is_current_member_wishlist': is_current_member_wishlist})

@app.route('/wishlist/<int:id>', methods=['DELETE'])
@requires_login
def delete_member_wishlist_item(id):
    # only allow delete own items
    item = WishlistItem.get_by_id(id)
    if item and item.owner_key == g.member.key:
        item.key.delete()
        return '', 200
    else:
        return BadRequest()

@app.route('/wishlist/<int:id>', methods=['PUT'])
@requires_login
def update_member_wishlist_item(id):
    status = request.json['status']
    item = WishlistItem.get_by_id(id)
    # only allow 'reserve' and 'lock' actions
    if item and status == 'open' or status == 'reserved' or status == 'locked':
        item.update_status(status, g.member.key)
        return jsonify({'owner_id': item.owner_key.id()})
    else:
        return BadRequest()

@app.route('/wishlist/members', methods=['GET'])
@requires_login
def get_members_with_wishlists():
    """ returns json in the form of:
        "members": {
            [
                "first_name": "Trung",
                "id": 12345678  // member's id
            ],
            ...
        }
    """
    member_wishlists = WishlistItem.query(projection=["owner_key"], group_by=["owner_key"]).fetch()
    members = [{'first_name': item.owner_key.get().first_name, 'id': item.owner_key.id()} for item in member_wishlists]
    return jsonify({'members': members})
