from app import requires_login
from flask import render_template
from app.views.main import app


@app.route('/wishlists')
@requires_login
def wishlists():
    return render_template('wishlists.html')
