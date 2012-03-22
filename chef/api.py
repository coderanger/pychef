import copy
import datetime
import itertools
import logging
import os
import re
import socket
import threading
import urllib2
import urlparse
import weakref

import pkg_resources

from chef.auth import sign_request
from chef.exceptions import ChefServerError
from chef.rsa import Key
from chef.utils import json
from chef.utils.file import walk_backwards

api_stack = threading.local()
log = logging.getLogger('chef.api')

def api_stack_value():
    if not hasattr(api_stack, 'value'):
        api_stack.value = []
    return api_stack.value


class UnknownRubyExpression(Exception):
    """Token exception for unprocessed Ruby expressions."""


class ChefRequest(urllib2.Request):
    """Workaround for using PUT/DELETE with urllib2."""
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        # Request is an old-style class, no super() allowed.
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        if self._method:
            return self._method
        return urllib2.Request.get_method(self)


class ChefAPI(object):
    """The ChefAPI object is a wrapper for a single Chef server.

    .. admonition:: The API stack

        PyChef maintains a stack of :class:`ChefAPI` objects to be use with
        other methods if an API object isn't given explicitly. The first
        ChefAPI created will become the default, though you can set a specific
        default using :meth:`ChefAPI.set_default`. You can also use a ChefAPI
        as a context manager to create a scoped default::

            with ChefAPI('http://localhost:4000', 'client.pem', 'admin'):
                n = Node('web1')
    """

    ruby_value_re = re.compile(r'#\{([^}]+)\}')

    def __init__(self, url, key, client, version='0.10.8'):
        self.url = url.rstrip('/')
        self.parsed_url = urlparse.urlparse(self.url)
        if not isinstance(key, Key):
            key = Key(key)
        self.key = key
        self.client = client
        self.version = version
        self.version_parsed = pkg_resources.parse_version(self.version)
        self.platform = self.parsed_url.hostname == 'api.opscode.com'
        if not api_stack_value():
            self.set_default()

    @classmethod
    def from_config_file(cls, path):
        """Load Chef API paraters from a config file. Returns None if the
        config can't be used.
        """
        log.debug('Trying to load from "%s"', path)
        if not os.path.isfile(path) or not os.access(path, os.R_OK):
            # Can't even read the config file
            log.debug('Unable to read config file "%s"', path)
            return
        url = key_path = client_name = None
        for line in open(path):
            if not line.strip() or line.startswith('#'):
                continue # Skip blanks and comments
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue # Not a simple key/value, we can't parse it anyway
            key, value = parts
            value = value.strip().strip('"\'')
            def _ruby_value(match):
                expr = match.group(1).strip()
                if expr == 'current_dir':
                    return os.path.dirname(path)
                log.debug('Unknown ruby expression in line "%s"', line)
                raise UnknownRubyExpression
            try:
                value = cls.ruby_value_re.sub(_ruby_value, value)
            except UnknownRubyExpression:
                continue
            if key == 'chef_server_url':
                url = value
            elif key == 'node_name':
                client_name = value
            elif key == 'client_key':
                # When http://tickets.opscode.com/browse/CHEF-2011 is resolved
                # there will need to be some post-processing here
                key_path = value
        if not url:
            # No URL, no chance this was valid
            log.debug('No Chef server URL found')
            return
        if not key_path:
            # Try and use ./client.pem
            key_path = os.path.join(os.path.dirname(path), 'client.pem')
        if not os.path.isfile(key_path) or not os.access(key_path, os.R_OK):
            # Can't read the client key
            log.debug('Unable to read key file "%s"', key_path)
            return
        if not client_name:
            client_name = socket.getfqdn()
        return cls(url, key_path, client_name)

    @staticmethod
    def get_global():
        """Return the API on the top of the stack."""
        while api_stack_value():
            api = api_stack_value()[-1]()
            if api is not None:
                return api
            del api_stack_value()[-1]

    def set_default(self):
        """Make this the default API in the stack. Returns the old default if any."""
        old = None
        if api_stack_value():
            old = api_stack_value().pop(0)
        api_stack_value().insert(0, weakref.ref(self))
        return old

    def __enter__(self):
        api_stack_value().append(weakref.ref(self))
        return self

    def __exit__(self, type, value, traceback):
        del api_stack_value()[-1]

    def _request(self, method, url, data, headers):
        # Testing hook, subclass and override for WSGI intercept
        request = ChefRequest(url, data, headers, method=method)
        return urllib2.urlopen(request).read()

    def request(self, method, path, headers={}, data=None):
        auth_headers = sign_request(key=self.key, http_method=method,
            path=self.parsed_url.path+path.split('?', 1)[0], body=data,
            host=self.parsed_url.netloc, timestamp=datetime.datetime.utcnow(),
            user_id=self.client)
        headers = dict((k.lower(), v) for k, v in headers.iteritems())
        headers['x-chef-version'] = self.version
        headers.update(auth_headers)
        try:
            response = self._request(method, self.url+path, data, dict((k.capitalize(), v) for k, v in headers.iteritems()))
        except urllib2.HTTPError, e:
            err = e.read()
            try:
                err = json.loads(err)
                raise ChefServerError.from_error(err['error'], code=e.code)
            except ValueError:
                pass
            raise
        return response

    def api_request(self, method, path, headers={}, data=None):    
        headers = dict((k.lower(), v) for k, v in headers.iteritems())
        headers['accept'] = 'application/json'
        if data is not None:
            headers['content-type'] = 'application/json'
            data = json.dumps(data)
        response = self.request(method, path, headers, data)
        return json.loads(response)

    def __getitem__(self, path):
        return self.api_request('GET', path)


def autoconfigure(base_path=None):
    """Try to find a knife or chef-client config file to load parameters from,
    starting from either the given base path or the current working directory.

    The lookup order mirrors the one from Chef, first all folders from the base
    path are walked back looking for .chef/knife.rb, then ~/.chef/knife.rb,
    and finally /etc/chef/client.rb.

    The first file that is found and can be loaded successfully will be loaded
    into a :class:`ChefAPI` object.
    """
    base_path = base_path or os.getcwd()
    # Scan up the tree for a knife.rb or client.rb. If that fails try looking
    # in /etc/chef. The /etc/chef check will never work in Win32, but it doesn't
    # hurt either.
    for path in walk_backwards(base_path):
        config_path = os.path.join(path, '.chef', 'knife.rb')
        api = ChefAPI.from_config_file(config_path)
        if api is not None:
            return api

    # The walk didn't work, try ~/.chef/knife.rb
    config_path = os.path.expanduser(os.path.join('~', '.chef', 'knife.rb'))
    api = ChefAPI.from_config_file(config_path)
    if api is not None:
        return api

    # Nothing in the home dir, try /etc/chef/client.rb
    config_path = os.path.join(os.path.sep, 'etc', 'chef', 'client.rb')
    api = ChefAPI.from_config_file(config_path)
    if api is not None:
        return api
