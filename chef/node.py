import collections

from chef.base import ChefObject
from chef.exceptions import ChefError

class NodeAttributes(collections.MutableMapping):
    
    def __init__(self, search_path=[], path=None, write=None):
        if not isinstance(search_path, collections.Sequence):
            search_path = [search_path]
        self.search_path = search_path
        self.path = path or ()
        self.write = write

    def __iter__(self):
        keys = set()
        for d in self.search_path:
            keys |= set(d.iterkeys())
        return iter(keys)

    def __len__(self):
        l = 0
        for key in self:
            l += 1
        return l

    def __getitem__(self, key):
        for d in self.search_path:
            if key in d:
                value = d[key]
                break
        else:
            raise KeyError(key)
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

    def __setitem__(self, key, value):
        if self.write is None:
            raise ChefError('This attribute is not writable')
        dest = self.write
        for path_key in self.path:
            dest = dest.setdefault(path_key, {})
        dest[key] = value

    def __delitem__(self, key):
        if self.write is None:
            raise ChefError('This attribute is not writable')
        dest = self.write
        for path_key in self.path:
            dest = dest.setdefault(path_key, {})
        del dest[key]

    def get_dotted(self, key):
        value = self
        for k in key.split('.'):
            if not isinstance(value, NodeAttributes):
                raise KeyError(key)
            value = value[k]
        return value

    def set_dotted(self, key, value):
        dest = self
        keys = key.split('.')
        last_key = keys.pop()
        for k in keys:
            if k not in dest:
                dest[k] = {}
            dest = dest[k]
            if not isinstance(dest, NodeAttributes):
                raise ChefError
        dest[last_key] = value

    def to_dict(self):
        merged = {}
        for d in reversed(self.search_path):
            merged.update(d)
        return merged


class Node(ChefObject):
    """A Chef node object.

    .. admonition:: Node attributes

        Node attributes can be accessed via the mapping API. This will perform
        the same merge as Chef, though it will not take roles or other sources
        of attribute data into account::

            n = Node('web1')
            print n['fqdn']
            n['apache']['log_dir'] = '/srv/log'

        Individual attribute levels ar available on named attributes::

            n.default['attr']
            n.normal['attr']
            n.override['attr']
            n.automatic['attr']

        A helper is available to get and set dotted attribute paths. Note that
        if one of the attribute keys includes a literal period, this will not
        work correctly and you must use the mapping API::

            n.attributes.get_dotted('apache.log_dir')
            n.attributes.set_dotted('apache.log_dir', '/srv/log')
    """

    url = '/nodes'
    attributes = {
        'default': NodeAttributes,
        'normal': lambda d: NodeAttributes(d, write=d),
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
