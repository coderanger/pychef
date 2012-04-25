from chef.base import ChefObject

class Environment(ChefObject):
    """A Chef environment object.

    .. versionadded:: 0.2
    """

    url = '/environments'
    
    api_version = '0.10'

    attributes = {
        'description': str,
        'cookbook_versions': dict,
        'default_attributes': dict,
        'override_attributes': dict,
    }
