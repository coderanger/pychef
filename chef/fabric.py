from chef.api import ChefAPI, autoconfigure
from chef.environment import Environment
from chef.exceptions import ChefError, ChefAPIVersionError
from chef.search import Search

class Roledef(object):
    """Represents a Fabric roledef for a Chef role."""
    def __init__(self, name, api, hostname_attr, environment=None):
        self.name = name
        self.api = api
        self.hostname_attr = hostname_attr
        if isinstance(self.hostname_attr, basestring):
            self.hostname_attr = (self.hostname_attr,)
        self.environment = environment

    def __call__(self):
        query = 'roles:%s' % self.name
        if self.environment:
            query += ' AND chef_environment:%s' % self.environment
        for row in Search('node', query, api=self.api):
            if row:
                if callable(self.hostname_attr):
                    yield self.hostname_attr(row.object)
                else:
                    for attr in self.hostname_attr:
                        try:
                            yield row.object.attributes.get_dotted(attr)
                            break
                        except KeyError:
                            continue
                    else:
                        raise ValueError('Cannot find a usable hostname attribute for node %s', row.object)


def chef_roledefs(api=None, hostname_attr=['cloud.public_hostname', 'fqdn'], environment='_default'):
    """Build a Fabric roledef dictionary from a Chef server.

    Example::

        from fabric.api import env, run, roles
        from chef.fabric import chef_roledefs

        env.roledefs = chef_roledefs()

        @roles('web_app')
        def mytask():
            run('uptime')

    ``hostname_attr`` can either be a string that is the attribute in the chef
    node that holds the hostname or IP to connect to, an array of such keys to
    check in order (the first which exists will be used), or a callable which
    takes a :class:`~chef.Node` and returns the hostname or IP to connect to.
    
    To refer to a nested attribute, separate the levels with '.' e.g. 'ec2.public_hostname'

    ``environment`` is the chef environment whose nodes will be fetched. The
    default environment is '_default'.

    .. versionadded:: 0.1

    .. versionadded:: 0.2
        Support for iterable and callable values for  the``hostname_attr``
        argument, and the ``environment`` argument.
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
