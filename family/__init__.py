from flask import Flask
from family.config import setup_config
from family.settings import setup_settings
from family.views import setup_views
from werkzeug.debug import DebuggedApplication


def create_app():
    flask_app = Flask(__name__)

    # load site settings from the database
    setup_settings(flask_app)

    # environment-aware configuration
    setup_config(flask_app)

    return flask_app


app = create_app()
app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

# Import views only AFTER 'app' is defined, the object is used in the view decorators
setup_views()
