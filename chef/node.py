import collections

from chef.base import ChefObject
from chef.exceptions import ChefError

class NodeAttributes(object):
    
    def __init__(self, search_path=[], path=None, write=None):
        if not isinstance(search_path, collections.Sequence):
            search_path = [search_path]
        self.search_path = search_path
        self.path = path or ()
        self.write = write

    def get(self, key, default=None):
        for d in self.search_path:
            if key in d:
                value = d[key]
                break
        else:
            return default
        if not isinstance(value, dict):
            return value
        new_search_path = []
        for d in self.search_path:
            new_d = d.get(key, {})
            if not isinstance(new_d, dict):
                # Structural mismatch
                new_d = {}
            new_search_path.append(new_d)
        return self.__class__(new_search_path, self.path+(key,), write=self.write)

    def __getitem__(self, key):
        token = object()
        value = self.get(key, token)
        if value is token:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        if self.write is None:
            raise ChefError('This attribute is not writable')
        dest = self.write
        for path_key in self.path:
            dest = dest.setdefault(path_key, {})
        dest[key] = value

    def get_dotted(self, key):
        value = self
        for k in key.split('.'):
            if not isinstance(value, NodeAttributes):
                raise KeyError(key)
            value = value[k]
        return value

    def to_dict(self):
        merged = {}
        for d in reversed(self.search_path):
            merged.update(d)
        return merged


class Node(ChefObject):
    """A single Chef node."""

    url = '/nodes'
    attributes = {
        'default': NodeAttributes,
        'normal': lambda d=None: NodeAttributes(d, write=d),
        'override': NodeAttributes,
        'automatic': NodeAttributes,
        'run_list': list,
    }

    def get(self, key, default=None):
        return self.attributes.get(key, default)

    def __getitem__(self, key):
        return self.attributes[key]

    def __setitem__(self, key, value):
        self.attributes[key] = value

    def _populate(self, data):
        if not self.exists:
            # Make this exist so the normal<->attributes cross-link will
            # function correctly
            data['normal'] = {}
        super(Node, self)._populate(data)
        self.attributes = NodeAttributes((data.get('automatic', {}),
                                          data.get('override', {}),
                                          data['normal'], # Must exist, see above
                                          data.get('default', {})), write=data['normal'])
