from chef.base import ChefObject

class Role(ChefObject):
    """A Chef role object."""

    url = '/roles'
    attributes = {
        'description': str,
        'run_list': list,
        'default_attributes': dict,
        'override_attributes': dict,
        'env_run_lists': dict
    }
