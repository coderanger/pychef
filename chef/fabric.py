from chef.api import ChefAPI, autoconfigure
from chef.environment import Environment
from chef.exceptions import ChefError, ChefAPIVersionError
from chef.search import Search

class Roledef(object):
    """Represents a Fabric roledef for a Chef role.
        
    hostname_attr can either be a string that is the attribute in the chef node that holds the real hostname.
    Or it can be a function that takes a Node object as a parameter and returns the attribute.
    """ 
    def __init__(self, name, api, hostname_attr, environment=None):
        self.name = name
        self.api = api
        self.hostname_attr = hostname_attr
        self.environment = environment

    def __call__(self):
        query = 'roles:%s' % self.name
        if self.environment:
            query += ' AND chef_environment:%s' % self.environment
        for row in Search('node', query, api=self.api):
            if row:
                attr = self.hostname_attr(row.object) if callable(self.hostname_attr) else self.hostname_attr
                yield row.object.attributes.get_dotted(attr)


def chef_roledefs(api=None, hostname_attr = 'fqdn', environment = '_default'):
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

    environment is the chef environment whose nodes will be fetched. The default environment is "_default".
    """
    api = api or ChefAPI.get_global() or autoconfigure()
    if not api:
        raise ChefError('Unable to load Chef API configuration')
    if api.version_parsed < Environment.api_version_parsed and environment is not None:
        raise ChefAPIVersionError('Environment support requires Chef API 0.10 or greater')
    roledefs = {}
    for row in Search('role', api=api):
        name = row['name']
        roledefs[name] =  Roledef(name, api, hostname_attr, environment)
    return roledefs
