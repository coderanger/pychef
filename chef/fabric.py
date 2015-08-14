import six
import functools

from chef.api import ChefAPI, autoconfigure
from chef.environment import Environment
from chef.exceptions import ChefError, ChefAPIVersionError
from chef.search import Search

try:
    from fabric.api import env, task, roles, output
except ImportError as e:
    env = {}
    task = lambda *args, **kwargs: lambda fn: fn
    roles = task

__all__ = ['chef_roledefs', 'chef_environment', 'chef_query', 'chef_tags']

# Default environment name
DEFAULT_ENVIRONMENT = '_default'

# Default hostname attributes
DEFAULT_HOSTNAME_ATTR = ['cloud.public_hostname', 'fqdn']

# Sentinel object to trigger defered lookup
_default_environment = object()

def _api(api):
    api = api or ChefAPI.get_global() or autoconfigure()
    if not api:
        raise ChefError('Unable to load Chef API configuration')
    return api


class Roledef(object):
    """Represents a Fabric roledef for a Chef role."""
    def __init__(self, query, api, hostname_attr, environment=None):
        self.query = query
        self.api = api
        self.hostname_attr = hostname_attr
        if isinstance(self.hostname_attr, six.string_types):
            self.hostname_attr = (self.hostname_attr,)
        self.environment = environment

    def __call__(self):
        query = self.query
        environment = self.environment
        if environment is _default_environment:
            environment = env.get('chef_environment', DEFAULT_ENVIRONMENT)
        if environment:
            query += ' AND chef_environment:%s' % environment
        for row in Search('node', query, api=self.api):
            if row:
                if callable(self.hostname_attr):
                    val = self.hostname_attr(row.object)
                    if val:
                        yield val
                else:
                    for attr in self.hostname_attr:
                        try:
                            val =  row.object.attributes.get_dotted(attr)
                            if val: # Don't ever give out '' or None, since it will error anyway
                                yield val
                                break
                        except KeyError:
                            pass # Move on to the next
                    else:
                        raise ChefError('Cannot find a usable hostname attribute for node %s', row.object)


def chef_roledefs(api=None, hostname_attr=DEFAULT_HOSTNAME_ATTR, environment=_default_environment):
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

    To refer to a nested attribute, separate the levels with ``'.'`` e.g. ``'ec2.public_hostname'``

    ``environment`` is the Chef :class:`~chef.Environment` name in which to
    search for nodes. If set to ``None``, no environment filter is added. If
    set to a string, it is used verbatim as a filter string. If not passed as
    an argument at all, the value in the Fabric environment dict is used,
    defaulting to ``'_default'``.

    .. note::

        ``environment`` must be set to ``None`` if you are emulating Chef API
        version 0.9 or lower.

    .. versionadded:: 0.1

    .. versionadded:: 0.2
        Support for iterable and callable values for  the``hostname_attr``
        argument, and the ``environment`` argument.
    """
    api = _api(api)
    if api.version_parsed < Environment.api_version_parsed and environment is not None:
        raise ChefAPIVersionError('Environment support requires Chef API 0.10 or greater')
    roledefs = {}
    for row in Search('role', api=api):
        name = row['name']
        roledefs[name] =  Roledef('roles:%s' % name, api, hostname_attr, environment)
    return roledefs


@task(alias=env.get('chef_environment_task_alias', 'env'))
def chef_environment(name, api=None):
    """A Fabric task to set the current Chef environment context.

    This task works alongside :func:`~chef.fabric.chef_roledefs` to set the
    Chef environment to be used in future role queries.

    Example::

        from chef.fabric import chef_environment, chef_roledefs
        env.roledefs = chef_roledefs()

    .. code-block:: bash

        $ fab env:production deploy

    The task can be configured slightly via Fabric ``env`` values.

    ``env.chef_environment_task_alias`` sets the task alias, defaulting to "env".
    This value must be set **before** :mod:`chef.fabric` is imported.

    ``env.chef_environment_validate`` sets if :class:`~chef.Environment` names
    should be validated before use. Defaults to True.

    .. versionadded:: 0.2
    """
    if env.get('chef_environment_validate', True):
        api = _api(api)
        chef_env = Environment(name, api=api)
        if not chef_env.exists:
            raise ChefError('Unknown Chef environment: %s' % name)
    env['chef_environment'] = name


def chef_query(query, api=None, hostname_attr=DEFAULT_HOSTNAME_ATTR, environment=_default_environment):
    """A decorator to use an arbitrary Chef search query to find nodes to execute on.

    This is used like Fabric's ``roles()`` decorator, but accepts a Chef search query.

    Example::

        from chef.fabric import chef_query

        @chef_query('roles:web AND tags:active')
        @task
        def deploy():
            pass

    .. versionadded:: 0.2.1
    """
    api = _api(api)
    if api.version_parsed < Environment.api_version_parsed and environment is not None:
        raise ChefAPIVersionError('Environment support requires Chef API 0.10 or greater')
    rolename = 'query_'+query
    env.setdefault('roledefs', {})[rolename] = Roledef(query, api, hostname_attr, environment)
    return lambda fn: roles(rolename)(fn)


def chef_tags(*tags, **kwargs):
    """A decorator to use Chef node tags to find nodes to execute on.

    This is used like Fabric's ``roles()`` decorator, but accepts a list of tags.

    Example::

        from chef.fabric import chef_tags

        @chef_tags('active', 'migrator')
        @task
        def migrate():
            pass

    .. versionadded:: 0.2.1
    """
    # Allow passing a single iterable
    if len(tags) == 1 and not isinstance(tags[0], six.string_types):
        tags = tags[0]
    query = ' AND '.join('tags:%s'%tag.strip() for tag in tags)
    return chef_query(query, **kwargs)
