import collections

from chef.api import ChefAPI
from chef.exceptions import ChefServerNotFoundError

class ChefQuery(collections.Mapping):
    def __init__(self, obj_class, names, api):
        self.obj_class = obj_class
        self.names = names
        self.api = api

    def __len__(self):
        return len(self.names)

    def __contains__(self, key):
        return key in self.names

    def __iter__(self):
        return iter(self.names)

    def __getitem__(self, name):
        if name not in self:
            raise KeyError('%s not found'%name)
        return self.obj_class(name, api=self.api)


class ChefObject(object):
    """A base class for Chef API objects."""

    url = ''
    attributes = {}

    def __init__(self, name, api=None, skip_load=False):
        self.name = name
        self.api = api or ChefAPI.get_global()
        self.url = self.__class__.url + '/' + self.name
        self.exists = False
        if not skip_load:
            try:
                data = self.api[self.url]
            except ChefServerNotFoundError:
                pass
            else:
                self.exists = True
        for name, cls in self.__class__.attributes.iteritems():
            if self.exists:
                value = cls(data[name])
            else:
                value = cls()
            setattr(self, name, value)

    @classmethod
    def list(cls, api=None):
        api = api or ChefAPI.get_global()
        names = [name for name, url in api[cls.url].iteritems()]
        return ChefQuery(cls, names, api)

    @classmethod
    def create(cls, name, api=None, **kwargs):
        api = api or ChefAPI.get_global()
        obj = cls(name, api, skip_load=True)
        for key, value in kwargs.iteritems():
            setattr(obj, key, value)
        api.api_request('POST', cls.url, data=obj)
        return obj

    def save(self, api=None):
        api = api or ChefAPI.get_global()
        try:
            api.api_request('PUT', self.url, data=self)
        except ChefServerNotFoundError, e:
            # If you get a 404 during a save, just create it instead
            # This mirrors the logic in the Chef code
            api.api_request('POST', self.__class__.url, data=self)

    def delete(self, api=None):
        api = api or ChefAPI.get_global()
        api.api_request('DELETE', self.url)

    def to_dict(self):
        d = {
            'name': self.name,
            'json_class': 'Chef::'+self.__class__.__name__,
            'chef_type': self.__class__.__name__.lower(),
        }
        for attr in self.__class__.attributes.iterkeys():
            d[attr] = getattr(self, attr)
        return d
