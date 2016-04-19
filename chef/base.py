import six
import collections

import pkg_resources
from chef.acl import Acl

from chef.api import ChefAPI
from chef.exceptions import *

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


class ChefObjectMeta(type):
    def __init__(cls, name, bases, d):
        super(ChefObjectMeta, cls).__init__(name, bases, d)
        if name != 'ChefObject':
            ChefObject.types[name.lower()] = cls
        cls.api_version_parsed = pkg_resources.parse_version(cls.api_version)


class ChefObject(six.with_metaclass(ChefObjectMeta, object)):
    """A base class for Chef API objects."""
    types = {}

    url = ''
    attributes = {}

    api_version = '0.9'

    def __init__(self, name, api=None, skip_load=False):
        self.name = name
        self.api = api or ChefAPI.get_global()
        self._check_api_version(self.api)

        self.url = self.__class__.url + '/' + self.name
        self.exists = False
        data = {}
        if not skip_load:
            try:
                data = self.api[self.url]
            except ChefServerNotFoundError:
                pass
            else:
                self.exists = True
        self._populate(data)

    def _populate(self, data):
        for name, cls in six.iteritems(self.__class__.attributes):
            if name in data:
                value = cls(data[name])
            else:
                value = cls()
            setattr(self, name, value)

    @classmethod
    def from_search(cls, data, api=None):
        obj = cls(data.get('name'), api=api, skip_load=True)
        obj.exists = True
        obj._populate(data)
        return obj

    @classmethod
    def list(cls, api=None):
        """Return a :class:`ChefQuery` with the available objects of this type.
        """
        api = api or ChefAPI.get_global()
        cls._check_api_version(api)
        names = [name for name, url in six.iteritems(api[cls.url])]
        return ChefQuery(cls, names, api)

    @classmethod
    def create(cls, name, api=None, **kwargs):
        """Create a new object of this type. Pass the initial value for any
        attributes as keyword arguments.
        """
        api = api or ChefAPI.get_global()
        cls._check_api_version(api)
        obj = cls(name, api, skip_load=True)
        for key, value in six.iteritems(kwargs):
            setattr(obj, key, value)
        api.api_request('POST', cls.url, data=obj)
        return obj

    def save(self, api=None):
        """Save this object to the server. If the object does not exist it
        will be created.
        """
        api = api or self.api
        try:
            api.api_request('PUT', self.url, data=self)
        except ChefServerNotFoundError as e:
            # If you get a 404 during a save, just create it instead
            # This mirrors the logic in the Chef code
            api.api_request('POST', self.__class__.url, data=self)

    def delete(self, api=None):
        """Delete this object from the server."""
        api = api or self.api
        api.api_request('DELETE', self.url)

    def to_dict(self):
        d = {
            'name': self.name,
            'json_class': 'Chef::'+self.__class__.__name__,
            'chef_type': self.__class__.__name__.lower(),
        }
        for attr in six.iterkeys(self.__class__.attributes):
            d[attr] = getattr(self, attr)
        return d

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %s>'%(type(self).__name__, self)

    @classmethod
    def _check_api_version(cls, api):
        # Don't enforce anything if api is None, since there is sometimes a
        # use for creating Chef objects without an API connection (just for
        # serialization perhaps).
        if api and cls.api_version_parsed > api.version_parsed:
            raise ChefAPIVersionError("Class %s is not compatible with API version %s" % (cls.__name__, api.version))

    def get_acl(self):
        return Acl(self.__class__.url.strip('/'), self.name, self.api)
