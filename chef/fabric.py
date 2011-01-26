from chef import Search
from chef.api import ChefAPI, autoconfigure
from chef.exceptions import ChefError

class Roledef(object):
    def __init__(self, name, api):
        self.name = name
        self.api = api

    def __call__(self):
        for row in Search('node', 'roles:'+self.name, api=self.api):
            yield row.object['fqdn']


def chef_roledefs(api=None):
    """Build a Fabric roledef dictionary from a Chef server.

    Example:

        from fabric.api import env, run, roles
        from chef.fabric import chef_roledefs

        env.roledefs = chef_roledefs()

        @roles('web_app')
        def mytask():
            run('uptime')
    """
    api = api or ChefAPI.get_global() or autoconfigure()
    if not api:
        raise ChefError('Unable to load Chef API configuration')
    roledefs = {}
    for row in Search('role', api=api):
        name = row['name']
        roledefs[name] =  Roledef(name, api)
    return roledefs
