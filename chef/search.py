import collections
import urllib

from chef.api import ChefAPI
from chef.base import ChefQuery
from chef.exceptions import ChefError

class SearchRow(dict):
    """A single row in a search result."""

    @property
    def object(self):
        pass
        # Not yet

class Search(collections.Sequence):
    """A search of the Chef index."""

    url = '/search'

    def __init__(self, index, query=None, sort=None, rows=None, start=None, api=None):
        self.index = index
        self.query = query
        self.sort = sort
        self.rows = rows
        self.start = start
        self.api = api or ChefAPI.get_global()
        self.url = self.__class__.url + '/' + self.index
        args = {}
        if self.query is not None:
            args['q'] = self.query
        if self.sort is not None:
            args['sort'] = self.sort
        if self.rows is not None:
            args['rows'] = self.rows
        if self.start is not None:
            args['start'] = self.start
        if args:
            self.url += '?' + urllib.urlencode(args)

    @property
    def data(self):
        if not hasattr(self, '_data'):
            self._data = self.api[self.url]
        return self._data

    def __len__(self):
        return self.data['total']

    def __getitem__(self, i):
        return SearchRow(self.data['rows'][i])

    def __contains__(self, name):
        for obj in self:
            if obj.get('name') == name:
                return True
        return False

    @classmethod
    def list(cls, api=None):
        api = api or ChefAPI.get_global()
        names = [name for name, url in api[cls.url].iteritems()]
        return ChefQuery(cls, names, api)
