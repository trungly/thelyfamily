from app.models.settings import Settings


class SiteSettings(object):

    @staticmethod
    def as_dict():
        settings = Settings.query().fetch()
        retval = dict()
        for setting in settings:
            retval[setting.name] = setting.value
        return retval

    @staticmethod
    def get(name, default=None):
        setting = Settings.query(Settings.name == name).fetch(1)
        if len(setting):
            return setting[0].value
        else:
            if default:
                return default
            else:
                raise KeyError

    @staticmethod
    def set(name, value):
        setting = Settings.query(Settings.name == name).fetch(1)
        if len(setting):
            setting = setting[0]
            setting.value = value
        else:
            setting = Settings(name=name, value=value)
        setting.put()


def setup_settings(app):
    def add_settings_to_context():
        return dict(settings=SiteSettings())
    app.context_processor(add_settings_to_context)
