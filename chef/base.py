from chef.api import ChefAPI

class DelayedAttribute(object):
    """Descriptor that calls ._populate() before access to implement lazy loading."""

    def __init__(self, attr):
        self.attr = attr

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if not getattr(instance, '_populated', False):
            instance._populate()
            instance._populated = True
        return getattr(instance, '_'+self.attr)


class ChefObjectMeta(type):
    """Metaclass for ChefObject to implement lazy attributes."""

    def __init__(cls, name, bases, d):
        for attr in cls.attributes:
            setattr(cls, attr, DelayedAttribute(attr))


class ChefObject(object):
    """A base class for Chef API objects."""

    __metaclass__ = ChefObjectMeta

    url = ''
    attributes = []

    def __init__(self, name, api=None):
        self.name = name
        self.api = api or ChefAPI.get_global()
        self.url = self.__class__.url + '/' + self.name

    @classmethod
    def list(cls, api=None):
        api = api or ChefAPI.get_global()
        for name, url in api[cls.url].iteritems():
            yield cls(name, api=api)

    def save(self, api=None):
        api = api or ChefAPI.get_global()
        api.api_request('PUT', self.url, data=self)

    def delete(self, api=None):
        api = api or ChefAPI.get_global()
        api.api_request('DELETE', self.url)

    def _populate(self):
        data = self.api[self.url]
        for attr in self.__class__.attributes:
            setattr(self, '_'+attr, data[attr])
