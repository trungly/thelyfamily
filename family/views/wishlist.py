from flask import render_template
from family.decorators import requires_login
from family import app


@app.route('/wishlists')
@requires_login
def wishlists():
    return render_template('wishlists.html')
