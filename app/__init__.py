from functools import wraps

from flask import Flask, g, flash, redirect, url_for
from app.config import configure_app
from werkzeug.debug import DebuggedApplication


def create_app():
    flask_app = Flask(__name__)

    # environment-aware configuration
    configure_app(flask_app)

    # import views
    # register_views(flask_app)

    return flask_app


app = create_app()
app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)


def requires_login(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if hasattr(g, 'member') and g.member:
            return func(*args, **kwargs)
        else:
            flash('You will need to log in before you can access this website', 'warning')
            return redirect(url_for('home'))

    return decorator


# Ensure all the views are loaded, but only AFTER app is defined, as it is used in view decorators
import views
