import yaml

from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import BadValueError


class Setting(ndb.Model):
    """
    Settings model
    """
    name = ndb.StringProperty()
    value = ndb.GenericProperty()


class SiteSettings(object):
    """
    A database-backed object that holds settings for the app.

    TODO: Consider changing all(as_name_value_list=True) to export() and set(name_value_list) as import(),
    ... thus making the simple dictionary format the 'native' format, while still supporting name-value list format
    """

    def __init__(self, app):
        """ Check if settings were initialized; if not, load them from initial_settings.yaml
        """
        if not self.get('settings.initialized'):
            f = open('initial_settings.yaml')
            data = yaml.safe_load(f)
            local_settings = data.pop('local.settings')
            if local_settings and isinstance(local_settings, dict):
                data.update(local_settings)
            f.close()
            data['settings.initialized'] = True
            try:
                self.set_all(data)
            except BadValueError, bve:
                app.logger.error('Could not load initial settings file. Check the format.')
                raise bve

    def get(self, name):
        setting = Setting.query(Setting.name == name).fetch(1)
        if len(setting):
            return setting[0].value
        else:
            return None

    def set(self, name, value):
        setting = Setting.query(Setting.name == name).fetch(1)
        if len(setting):
            setting = setting[0]
            setting.value = value
        else:
            setting = Setting(name=name, value=value)
        setting.put()

    def get_all(self, as_name_value_list=False):
        """
        All the settings as a simple dictionary:
            { setting1: 'value1', setting2: 'value2', ... }
        Or, a name-value list:
            [
                { name: 'setting1', value: 'value1' },
                { name: 'setting2', value: 'value2' },
                ...
            ]
        """
        settings_from_db = Setting.query().fetch()
        if as_name_value_list:
            retval = []
            for setting in settings_from_db:
                retval.append({'name': setting.name, 'value': setting.value})
        else:
            retval = dict()
            for setting in settings_from_db:
                retval[setting.name] = setting.value

        return retval

    def set_all(self, settings):
        for setting in settings:
            if isinstance(setting, basestring):
                self.set(setting, settings[setting])
            elif isinstance(setting, dict):
                # name-value list
                self.set(setting['name'], setting['value'])

    def as_yaml(self):
        return {str(key): str(value) for key, value in self.get_all().iteritems()}


def setup_settings(app):
    """ Instantiate settings object and add them to the template contexts
    """
    app.settings = SiteSettings(app)

    def add_settings_to_context():
        return dict(settings=app.settings.get_all())
    app.context_processor(add_settings_to_context)
