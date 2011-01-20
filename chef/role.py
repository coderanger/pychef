from chef.base import ChefObject

class Role(ChefObject):
    """A model object for a Chef role."""

    url = '/roles'
    attributes = [
        'description',
        'run_list',
    ]

