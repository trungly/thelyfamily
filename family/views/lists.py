from flask import render_template

from family import app


@app.route('/lists', methods=['GET'])
def lists():
    return render_template('lists.html')
