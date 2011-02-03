from chef.base import ChefObject

class Role(ChefObject):
    """A Chef role object."""

    url = '/roles'
    attributes = {
        'description': str,
        'run_list': list,
    }
