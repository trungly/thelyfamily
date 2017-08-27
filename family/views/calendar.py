from family import app
from family.decorators import requires_login
from flask.json import jsonify
from flask.templating import render_template


@app.route('/calendar', methods=['GET'])
@requires_login
def calendar():
    return render_template('calendar.html')


@app.route('/calendar/events', methods=['GET'])
@requires_login
def calendar_events():
    """
    If you have an error you can return:
    {
        "success": 0,
        "error": "error message here"
    }
    :return:
    """
    events = {
        "success": 1,
        "result": [
            {
                "id": 293,
                "title": "Event 1",
                "url": "http://example.com",
                "class": "event-important",
                "start": 1461394420000,
                "end": 1461395520000
            },
        ]
    }
    return jsonify(events)
