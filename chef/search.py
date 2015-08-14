import six
import collections
import copy
import six.moves.urllib.parse

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
            if chef_class == 'ApiClient':
                chef_class = 'Client' # Special case since I don't match the Ruby name.
            cls = ChefObject.types.get(chef_class.lower())
            if not cls:
                raise ValueError('Unknown class %s'%chef_class)
            self._object = cls.from_search(self, api=self.api)
        return self._object


class Search(collections.Sequence):
    """A search of the Chef index.
    
    The only required argument is the index name to search (eg. node, role, etc).
    The second, optional argument can be any Solr search query, with the same semantics
    as Chef.
    
    Example::
    
        for row in Search('node', 'roles:app'):
            print row['roles']
            print row.object.name
    
    .. versionadded:: 0.1
    """

    url = '/search'

    def __init__(self, index, q='*:*', rows=1000, start=0, api=None):
        self.name = index
        self.api = api or ChefAPI.get_global()
        self._args = dict(q=q, rows=rows, start=start)
        self.url = self.__class__.url + '/' + self.name + '?' + six.moves.urllib.parse.urlencode(self._args)

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
        if isinstance(value, six.string_types):
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
        names = [name for name, url in six.iteritems(api[cls.url])]
        return ChefQuery(cls, names, api)
