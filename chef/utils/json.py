from __future__ import absolute_import
import types
try:
    import json
except ImportError:
    import simplejson as json

def maybe_call(x):
    if callable(x):
        return x()
    return x

class JSONEncoder(json.JSONEncoder):
    """Custom encoder to allow arbitrary classes."""

    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return maybe_call(obj.to_dict)
        elif hasattr(obj, 'to_list'):
            return maybe_call(obj.to_list)
        elif isinstance(obj, types.GeneratorType):
            return list(obj)
        return super(JSONEncoder, self).default(obj)

loads = json.loads
dumps = lambda obj, **kwargs: json.dumps(obj, cls=JSONEncoder, **kwargs)
