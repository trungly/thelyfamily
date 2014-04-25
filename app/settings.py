from app.models.settings import Setting
from google.appengine.api.datastore_errors import BadValueError


class SiteSettings(object):
    """
    TODO: Currently, this is just a collection of static methods;
    Explore making this a class that when instantiated holds a reference to a list of Setting (model) objects
    """

    @staticmethod
    def as_dict():
        """
        E.g.
        { setting1: 'value1', setting2: 'value2', ... }
        """
        settings = Setting.query().fetch()
        retval = dict()
        for setting in settings:
            retval[setting.name] = setting.value
        return retval

    @staticmethod
    def as_name_value_list():
        """
        E.g.
        [
            { name: 'setting1', value: 'value1' },
            { name: 'setting2', value: 'value2' },
            ...
        ]
        """
        settings = Setting.query().fetch()
        retval = []
        for setting in settings:
            retval.append({'name': setting.name, 'value': setting.value})
        return retval

    @staticmethod
    def get(name, default=None):
        setting = Setting.query(Setting.name == name).fetch(1)
        if len(setting):
            return setting[0].value
        else:
            return default

    @staticmethod
    def set(name, value):
        setting = Setting.query(Setting.name == name).fetch(1)
        if len(setting):
            setting = setting[0]
            setting.value = value
        else:
            setting = Setting(name=name, value=value)
        setting.put()

    @staticmethod
    def update(settings):
        for setting in settings:
            if isinstance(setting, Setting):
                SiteSettings.set(setting.name, settings.value)
            else:  # then assume dict
                SiteSettings.set(setting['name'], setting['value'])


def setup_settings(app):
    """ Check if settings were initialized; if not, load them from initial_settings.yaml
    Next, add settings object to the template contexts
    """
    if not SiteSettings.get('settings.initialized', None):
        import yaml
        f = open('initial_settings.yaml')
        # use safe_load instead load
        data = yaml.safe_load(f)
        f.close()
        data['settings.initialized'] = True
        try:
            SiteSettings.update(data)
        except BadValueError, bve:
            app.logger.error('Could not load initial settings file. Check the format.')
            raise bve

    def add_settings_to_context():
        return dict(settings=SiteSettings())
    app.context_processor(add_settings_to_context)
