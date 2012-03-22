import collections
import copy
import urllib

from chef.api import ChefAPI
from chef.base import ChefQuery, ChefObject

class SearchRow(dict):
    """A single row in a search result."""

    def __init__(self, row, api):
        super(SearchRow, self).__init__(row)
        self.api = api
        self._object = None

    @property
    def object(self):
        if self._object is  None:
            # Decode Chef class name
            chef_class = self.get('json_class', '')
            if chef_class.startswith('Chef::'):
                chef_class = chef_class[6:]
            cls = ChefObject.types.get(chef_class.lower())
            if not cls:
                raise ValueError('Unknown class %s'%chef_class)
            self._object = cls.from_search(self, api=self.api)
        return self._object


class Search(collections.Sequence):
    """A search of the Chef index."""

    url = '/search'

    def __init__(self, index, q='*:*', rows=1000, start=0, api=None):
        self.name = index
        self.api = api or ChefAPI.get_global()
        self._args = dict(q=q, rows=rows, start=start)
        self.url = self.__class__.url + '/' + self.name + '?' + urllib.urlencode(self._args)

    @property
    def data(self):
        if not hasattr(self, '_data'):
            self._data = self.api[self.url]
        return self._data

    @property
    def total(self):
        return self.data['total']

    def query(self, query):
        args = copy.copy(self._args)
        args['q'] = query
        return self.__class__(self.name, api=self.api, **args)

    def rows(self, rows):
        args = copy.copy(self._args)
        args['rows'] = rows
        return self.__class__(self.name, api=self.api, **args)

    def start(self, start):
        args = copy.copy(self._args)
        args['start'] = start
        return self.__class__(self.name, api=self.api, **args)

    def __len__(self):
        return len(self.data['rows'])

    def __getitem__(self, value):
        if isinstance(value, slice):
            if value.step is not None and value.step != 1:
                raise ValueError('Cannot use a step other than 1')
            return self.start(self._args['start']+value.start).rows(value.stop-value.start)
        if isinstance(value, basestring):
            return self[self.index(value)]
        row_value = self.data['rows'][value]
        # Check for null rows, just in case
        if row_value is None:
            return None
        return SearchRow(row_value, self.api)

    def __contains__(self, name):
        for row in self:
            if row.object.name == name:
                return True
        return False

    def index(self, name):
        for i, row in enumerate(self):
            if row.object.name == name:
                return i
        raise ValueError('%s not in search'%name)

    def __call__(self, query):
        return self.query(query)

    @classmethod
    def list(cls, api=None):
        api = api or ChefAPI.get_global()
        names = [name for name, url in api[cls.url].iteritems()]
        return ChefQuery(cls, names, api)
