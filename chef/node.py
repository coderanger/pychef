from chef.api import ChefAPI
from chef.exceptions import ChefError

class NodeAttributes(object):
    
    def __init__(self, search_path, path=None, write=None):
        self.search_path = search_path
        self.path = path or ()
        self.write = write
    
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
    
    def to_dict(self):
        merged = {}
        for d in reversed(self.search_path):
            merged.update(d)
        return merged
        

class _NodeDelayedAttr(object):
    """Descriptor that calls ._populate() before access to implement lazy loading."""
    
    def __init__(self, attr):
        self.attr = attr
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        instance._populate()
        return getattr(instance, '_'+self.attr)


class Node(object):
    """A single Chef node."""
    
    def __init__(self, name, api=None):
        self.name = name
        self.api = api or ChefAPI.get_global()
        self._populated = False
    
    @classmethod
    def list(cls, api=None):
        api = api or ChefAPI.get_global()
        for name, url in api['/nodes'].iteritems():
            yield cls(name, api=api)
    
    def save(self, api=None):
        api = api or ChefAPI.get_global()
        api.api_request('PUT', '/nodes/'+self.name, data=self)
            
    def __getitem__(self, key):
        self._populate()
        return self._attributes[key]
    
    def __setitem__(self, key, value):
        self._populate()
        self._attributes[key] = value
    
    def _populate(self):
        if self._populated:
            return
        data = self.api['/nodes/'+self.name]
        self._default = NodeAttributes((data['default'],))
        self._normal = NodeAttributes((data['normal'],), write=data['normal'])
        self._override = NodeAttributes((data['override'],))
        self._automatic = NodeAttributes((data['automatic'],))
        self._attributes = NodeAttributes((data['automatic'], data['override'], data['normal'], data['default']), write=data['normal'])
        self._run_list = data['run_list']
        self._populated = True
    
    # Lazy attributes
    default = _NodeDelayedAttr('default')
    normal = _NodeDelayedAttr('normal')
    override = _NodeDelayedAttr('override')
    automatic = _NodeDelayedAttr('automatic')
    attributes = _NodeDelayedAttr('attributes')
    run_list = _NodeDelayedAttr('run_list')
    
    def to_dict(self):
        """Convert to a dict in the same format as Chef::Node.to_json()."""
        return {
            'name': self.name,
            'json_class': 'Chef::Node',
            'automatic': self.automatic.to_dict(),
            'normal': self.normal.to_dict(),
            'chef_type': 'node',
            'default': self.default.to_dict(),
            'override': self.override.to_dict(),
            'run_list': self.run_list,
        }
    
    def __repr__(self):
        return '<Node %s>'%self.name
