from chef.base import ChefObject

class Role(ChefObject):
    """A model object for a Chef role."""

    url = '/roles'
    attributes = {
        'description': str,
        'run_list': list,
    }
