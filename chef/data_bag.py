import abc
import collections

from chef.base import ChefObject, ChefQuery, ChefObjectMeta

class DataBagMeta(ChefObjectMeta, abc.ABCMeta):
    """A metaclass to allow DataBag to use multiple inheritance."""

class DataBag(ChefObject, ChefQuery):
    __metaclass__ = DataBagMeta
    
    url = '/data'
    
    def _populate(self, data):
        self.obj_class = DataBagItem
        self.names = data.keys()
        self.parent = self

class DataBagItem(ChefObject, collections.Mapping):
    __metaclass__ = DataBagMeta

    url = '/data'

    def __init__(self, name, api=None, skip_load=False, parent=None):
        self.bag = parent
        super(DataBagItem, self).__init__(parent.name+'/'+name, api=api, skip_load=skip_load)
        self.name = name

    def _populate(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key):
        return self.data[key]
