from chef import Search
from chef.api import ChefAPI, autoconfigure
from chef.exceptions import ChefError

class Roledef(object):
    """Represents a Fabric roledef for a Chef role.
        
    hostname_attr can either be a string that is the attribute in the chef node that holds the real hostname.
    Or it can be a function that takes a Node object as a parameter and returns the attribute.
    """ 
    def __init__(self, name, api, hostname_attr):
        self.name = name
        self.api = api
        self.hostname_attr = hostname_attr 

    def __call__(self):
        for row in Search('node', 'roles:'+self.name, api=self.api):
            attr = self.hostname_attr(row.object) if callable(self.hostname_attr) else self.hostname_attr
            yield row.object.attributes.get_dotted(attr)


def chef_roledefs(api=None, hostname_attr = 'fqdn'):
    """Build a Fabric roledef dictionary from a Chef server.

    Example:

        from fabric.api import env, run, roles
        from chef.fabric import chef_roledefs

        env.roledefs = chef_roledefs()

        @roles('web_app')
        def mytask():
            run('uptime')

    hostname_attr can either be a string that is the attribute in the chef node that holds the real hostname.
    Or it can be a function that takes a Node object as a parameter and returns the attribute.
    
    To refer to a nested attribute, separate the levels with '.' e.g. 'ec2.public_hostname'

    For example:
        def use_ec2_hostname(node):
            if node.attributes.has_dotted('fqdn'):
              return 'fqdn'
            else:
              return 'ec2.public_hostname'
      
        env.roledefs = chef_roledefs(hostname_attr = use_ec2_hostname)

    """
    api = api or ChefAPI.get_global() or autoconfigure()
    if not api:
        raise ChefError('Unable to load Chef API configuration')
    roledefs = {}
    for row in Search('role', api=api):
        name = row['name']
        roledefs[name] =  Roledef(name, api, hostname_attr)
    return roledefs
