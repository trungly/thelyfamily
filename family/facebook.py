from flask import current_app


class Facebook(object):

    @staticmethod
    def access_token_url(code):
        url = 'https://graph.facebook.com/oauth/access_token?client_id={app_id}&redirect_uri={redirect_uri}&client_secret={app_secret}&code={code}'.format(
            app_id=current_app.settings.get('facebook.app.id'),
            redirect_uri='http://%s/facebook/return' % current_app.settings.get('host.name'),
            app_secret=current_app.settings.get('facebook.app.secret'),
            code=code
        )
        return url

    @staticmethod
    def debug_token_url(access_token):
        """ Facebook's auth API's are really confusing. This one is called 'Inspect access tokens' in the docs:
        https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow/#confirm
        In this one, input_token is the token you're inspecting (which was the user's access_token previously).
        And here, access_token is the lyfam's access token.
        We're mainly using it to get to the user's userid in order to store in the database
        """
        url = 'https://graph.facebook.com/debug_token?input_token={input_token}&access_token={access_token}'.format(
            input_token=access_token,
            access_token=current_app.settings.get('facebook.access.token')
        )
        return url

    @staticmethod
    def uploaded_photos_url(facebook_user):
        url = 'https://graph.facebook.com/{userid}/photos/uploaded?access_token={access_token}'.format(
            userid=facebook_user.userid,
            access_token=facebook_user.access_token,
        )
        return url
