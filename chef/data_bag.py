import abc
import collections

from chef.api import ChefAPI
from chef.base import ChefObject, ChefQuery, ChefObjectMeta
from chef.exceptions import ChefError

class DataBagMeta(ChefObjectMeta, abc.ABCMeta):
    """A metaclass to allow DataBag to use multiple inheritance."""


class DataBag(ChefObject, ChefQuery):
    __metaclass__ = DataBagMeta

    url = '/data'

    def _populate(self, data):
        self.obj_class = DataBagItem
        self.names = data.keys()

    def __getitem__(self, name):
        if name not in self:
            raise KeyError('%s not found'%name)
        return self.obj_class(self, name, api=self.api)


class DataBagItem(ChefObject, collections.MutableMapping):
    __metaclass__ = DataBagMeta

    url = '/data'
    attributes = {
        'raw_data': dict,
    }

    def __init__(self, bag, name, api=None, skip_load=False):
        self._bag = bag
        super(DataBagItem, self).__init__(str(bag)+'/'+name, api=api, skip_load=skip_load)
        self.name = name

    @property
    def bag(self):
        if not isinstance(self._bag, DataBag):
            self._bag = DataBag(self._bag, api=self.api)
        return self._bag

    @classmethod
    def from_search(cls, data, api):
        bag = data.get('data_bag')
        if not bag:
            raise ChefError('No data_bag key in data bag item information')
        name = data.get('name')
        if not name:
            raise ChefError('No name key in the data bag item information')
        item = name[len('data_bag_item_' + bag + '_'):]
        obj = cls(bag, item, api=api, skip_load=True)
        obj.exists = True
        obj._populate(data)
        return obj

    def _populate(self, data):
        if 'json_class' in data:
            self.raw_data = data['raw_data']
        else:
            self.raw_data = data

    def __len__(self):
        return len(self.raw_data)

    def __iter__(self):
        return iter(self.raw_data)

    def __getitem__(self, key):
        return self.raw_data[key]

    def __setitem__(self, key, value):
        self.raw_data[key] = value

    def __delitem__(self, key):
        del self.raw_data[key]

    @classmethod
    def create(cls, bag, name, api=None, **kwargs):
        api = api or ChefAPI.get_global()
        obj = cls(bag, name, api, skip_load=True)
        for key, value in kwargs.iteritems():
            obj[key] = value
        obj['id'] = name
        api.api_request('POST', cls.url+'/'+str(bag), data=obj.raw_data)
        if isinstance(bag, DataBag) and name not in bag.names:
            # Mutate the bag in-place if possible, so it will return the new
            # item instantly
            bag.names.append(name)
        return obj

    def save(self, api=None):
        api = api or self.api
        self['id'] = self.name
        try:
            api.api_request('PUT', self.url, data=self.raw_data)
        except ChefServerNotFoundError, e:
            api.api_request('POST', self.__class__.url+'/'+str(self._bag), data=self.raw_data)
