import os

from family.settings import SiteSettings


def setup_config(app):
    config = app.config

    config['SECRET_KEY'] = SiteSettings.get('secret.key')
    if 'localhost' in os.environ.get('SERVER_NAME', ''):
        config['DEBUG'] = True
    else:
        config['TRAP_HTTP_EXCEPTIONS'] = True
