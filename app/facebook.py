from flask import url_for


class Facebook(object):

    @staticmethod
    def auth_url():
        url = 'https://www.facebook.com/dialog/oauth?client_id={app_id}&redirect_uri={redirect_uri}&scope={scope}'.format(
            app_id='254341781341297',
            redirect_uri='http://localhost:8080/facebook/return',
            scope='user_photos'
        )
        return url

    @staticmethod
    def access_token_url(code):
        url = 'https://graph.facebook.com/oauth/access_token?client_id={app_id}&redirect_uri={redirect_uri}&client_secret={app_secret}&code={code}'.format(
            app_id='254341781341297',
            redirect_uri='http://localhost:8080/facebook/return',
            app_secret='aa5fd19f9925dc31919cca4675ec1246',  # TODO: configurize
            code=code
        )
        return url

    @staticmethod
    def debug_token_url(access_token):
        """ Facebook's auth API's are really confusing. This one is called 'Inspect access tokens' in the docs:
        https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow/#confirm
        In this one, input_token is the token you're inspecting (which was the user's access_token previously).
        And here, access_token is the app's token.
        """
        app_token = '254341781341297|LI7-LXnYyQ9SeYr0XYnOzvNJBQQ'  # obtained by going to:
        # https://graph.facebook.com/oauth/access_token?client_id=254341781341297&client_secret=aa5fd19f9925dc31919cca4675ec1246&grant_type=client_credentials

        url = 'https://graph.facebook.com/debug_token?input_token={input_token}&access_token={access_token}'.format(
            input_token=access_token,
            access_token=app_token
        )
        return url

    @staticmethod
    def uploaded_photos_url(facebook_user):
        url = 'https://graph.facebook.com/{userid}/photos/uploaded?access_token={access_token}'.format(
            userid=facebook_user.userid,
            access_token=facebook_user.access_token,
        )
        return url
