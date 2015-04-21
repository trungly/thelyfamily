from flask import request, render_template, jsonify

from family import app
from family.models.list import List


@app.route('/lists', methods=['GET'])
def lists():
    return render_template('lists.html')


@app.route('/api/lists', methods=['GET'])
def get_lists():
    all_lists = List.query().fetch()
    return jsonify({'data': all_lists})


@app.route('/api/lists', methods=['POST'])
def create_list():
    new_list = List(**request.json)
    new_list.put()
    return '', 200
