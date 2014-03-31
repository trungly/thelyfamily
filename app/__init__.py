from functools import wraps

from flask import Flask, g, flash, redirect, url_for
from app.config import configure_app


app = Flask(__name__.split('.')[0])

configure_app(app)


def requires_login(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if hasattr(g, 'member') and g.member:
            return func(*args, **kwargs)
        else:
            flash('You will need to log in before you can access this website', 'warning')
            return redirect(url_for('home'))

    return decorator


import views
