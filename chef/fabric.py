from chef import Search
from chef.api import ChefAPI, autoconfigure
from chef.exceptions import ChefError

class Roledef(object):
    def __init__(self, name, api, hostname_attr, environment):
        self.name = name
        self.api = api
        self.hostname_attr = hostname_attr
        self.environment = environment
	
    
    def __call__(self):
        if map(int, self.api.version.split(".")) >= [0, 10]:
            query = 'roles:%s AND chef_environment:%s' % (self.name, self.environment)
        else:
            query = 'roles:%s' % self.name

        for row in Search('node', query, api=self.api):
	    if row:	
	            yield row.object.attributes.get_dotted(self.hostname_attr)


def chef_roledefs(api=None, hostname_attr = 'fqdn', environment = "_default"):
    """Build a Fabric roledef dictionary from a Chef server.

    Example:

        from fabric.api import env, run, roles
        from chef.fabric import chef_roledefs

        env.roledefs = chef_roledefs()

        @roles('web_app')
        def mytask():
            run('uptime')
            
    hostname_attr is the attribute in the chef node that holds the real hostname.
    to refer to a nested attribute, separate the levels with '.'.
    for example 'ec2.public_hostname'
    environment is the chef environment whose nodes will be fetched. The default environment is "_default".
    """
    api = api or ChefAPI.get_global() or autoconfigure()
    if not api:
        raise ChefError('Unable to load Chef API configuration')
    roledefs = {}
    for row in Search('role', api=api):
        name = row['name']
        roledefs[name] =  Roledef(name, api, hostname_attr, environment)
    return roledefs
