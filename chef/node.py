import six
import collections

from chef.base import ChefObject
from chef.exceptions import ChefError

class NodeAttributes(collections.MutableMapping):
    """A collection of Chef :class:`~chef.Node` attributes.

    Attributes can be accessed like a normal python :class:`dict`::

        print node['fqdn']
        node['apache']['log_dir'] = '/srv/log'

    When writing to new attributes, any dicts required in the hierarchy are
    created automatically.

    .. versionadded:: 0.1
    """

    def __init__(self, search_path=[], path=None, write=None):
        if not isinstance(search_path, collections.Sequence):
            search_path = [search_path]
        self.search_path = search_path
        self.path = path or ()
        self.write = write

    def __iter__(self):
        keys = set()
        for d in self.search_path:
            keys |= set(six.iterkeys(d))
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

    def has_dotted(self, key):
        """Check if a given dotted key path is present. See :meth:`.get_dotted`
        for more information on dotted paths.

        .. versionadded:: 0.2
        """
        try:
            self.get_dotted(key)
        except KeyError:
            return False
        else:
            return True

    def get_dotted(self, key):
        """Retrieve an attribute using a dotted key path. A dotted path
        is a string of the form `'foo.bar.baz'`, with each `.` separating
        hierarcy levels.

        Example::

            node.attributes['apache']['log_dir'] = '/srv/log'
            print node.attributes.get_dotted('apache.log_dir')
        """
        value = self
        for k in key.split('.'):
            if not isinstance(value, NodeAttributes):
                raise KeyError(key)
            value = value[k]
        return value

    def set_dotted(self, key, value):
        """Set an attribute using a dotted key path. See :meth:`.get_dotted`
        for more information on dotted paths.

        Example::

            node.attributes.set_dotted('apache.log_dir', '/srv/log')
        """
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

    The Node object can be used as a dict-like object directly, as an alias for
    the :attr:`.attributes` data::

        >>> node = Node('name')
        >>> node['apache']['log_dir']
        '/var/log/apache2'

    .. versionadded:: 0.1

    .. attribute:: attributes

        :class:`~chef.node.NodeAttributes` corresponding to the composite of all
        precedence levels. This only uses the stored data on the Chef server,
        it does not merge in attributes from roles or environments on its own.

        ::

            >>> node.attributes['apache']['log_dir']
            '/var/log/apache2'

    .. attribute:: run_list

        The run list of the node. This is the unexpanded list in ``type[name]``
        format.

        ::

            >>> node.run_list
            ['role[base]', 'role[app]', 'recipe[web]']

    .. attribute:: chef_environment

        The name of the Chef :class:`~chef.Environment` this node is a member
        of. This value will still be present, even if communicating with a Chef
        0.9 server, but will be ignored.

        .. versionadded:: 0.2

    .. attribute:: default

        :class:`~chef.node.NodeAttributes` corresponding to the ``default``
        precedence level.

    .. attribute:: normal

        :class:`~chef.node.NodeAttributes` corresponding to the ``normal``
        precedence level.

    .. attribute:: override

        :class:`~chef.node.NodeAttributes` corresponding to the ``override``
        precedence level.

    .. attribute:: automatic

        :class:`~chef.node.NodeAttributes` corresponding to the ``automatic``
        precedence level.
    """

    url = '/nodes'
    attributes = {
        'default': NodeAttributes,
        'normal': lambda d: NodeAttributes(d, write=d),
        'override': NodeAttributes,
        'automatic': NodeAttributes,
        'run_list': list,
        'chef_environment': str
    }

    def has_key(self, key):
      return self.attributes.has_dotted(key)

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
        data.setdefault('chef_environment', '_default')
        super(Node, self)._populate(data)
        self.attributes = NodeAttributes((data.get('automatic', {}),
                                          data.get('override', {}),
                                          data['normal'], # Must exist, see above
                                          data.get('default', {})), write=data['normal'])

    def cookbooks(self, api=None):
        api = api or self.api
        return api[self.url + '/cookbooks']
