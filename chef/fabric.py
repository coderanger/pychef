from chef import Search
from chef.api import ChefAPI, autoconfigure
from chef.exceptions import ChefError

class Roledef(object):
    def __init__(self, name, api, hostname_attr):
        self.name = name
        self.api = api
	self.hostname_attr = hostname_attr
	
    def getSubAttribute(self, _dict, attr):
        attrs = attr.split('.')
        d = None #dict.get(attrs[0], None)
        for i in xrange(len(attrs)):
            _d = (d or _dict).get(attrs[i], None)
            if not _d:
                break
            d = _d

        return d



    def __call__(self):
        for row in Search('node', 'roles:'+self.name, api=self.api):
            print row.object, type(row.object)
            yield self.getSubAttribute(row.object, self.hostname_attr)


def chef_roledefs(api=None, hostname_attr = 'fqdn'):
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
        roledefs[name] =  Roledef(name, api, hostname_attr)
    return roledefs
