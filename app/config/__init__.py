import os


def configure_app(app):
    """ Set up this app
    """
    config = app.config

    # First, load the main settings
    config.from_object('app.config.production')

    # Next, if we are developing locally, load the local settings (overriding any previous settings)
    if 'localhost' in os.environ.get('SERVER_NAME', []):
        config.from_object('app.config.local')

    # Lastly, set up Instagram and Facebook urls
    url = 'https://instagram.com/oauth/authorize/?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code'
    config['INSTAGRAM_AUTH_URL'] = url.format(
        client_id=config['INSTAGRAM_CLIENT_ID'],
        redirect_uri='http://%s/photos/return' % config['HOST_NAME'],
    )

    url = 'https://www.facebook.com/dialog/oauth?client_id={app_id}&redirect_uri={redirect_uri}&scope={scope}'
    config['FACEBOOK_AUTH_URL'] = url.format(
        app_id=config['FACEBOOK_APP_ID'],
        redirect_uri='http://%s/facebook/return' % config['HOST_NAME'],
        scope='user_photos'
    )
