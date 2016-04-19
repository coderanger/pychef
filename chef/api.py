import datetime
import logging
import os
import re
import socket
import subprocess
import threading
import weakref
import six

import pkg_resources

import requests

from chef.auth import sign_request
from chef.exceptions import ChefServerError
from chef.rsa import Key
from chef.utils import json
from chef.utils.file import walk_backwards

api_stack = threading.local()
log = logging.getLogger('chef.api')

config_ruby_script = """
require 'chef'
Chef::Config.from_file('%s')
puts Chef::Config.configuration.to_json
""".strip()

def api_stack_value():
    if not hasattr(api_stack, 'value'):
        api_stack.value = []
    return api_stack.value


class UnknownRubyExpression(Exception):
    """Token exception for unprocessed Ruby expressions."""


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
    env_value_re = re.compile(r'ENV\[(.+)\]')
    ruby_string_re = re.compile(r'^\s*(["\'])(.*?)\1\s*$')

    def __init__(self, url, key, client, version='0.10.8', headers={}, ssl_verify=True):
        self.url = url.rstrip('/')
        self.parsed_url = six.moves.urllib.parse.urlparse(self.url)
        if not isinstance(key, Key):
            key = Key(key)
        if not key.key:
            raise ValueError("ChefAPI attribute 'key' was invalid.")
        self.key = key
        self.client = client
        self.version = version
        self.headers = dict((k.lower(), v) for k, v in six.iteritems(headers))
        self.version_parsed = pkg_resources.parse_version(self.version)
        self.platform = self.parsed_url.hostname == 'api.opscode.com'
        self.ssl_verify = ssl_verify
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
        ssl_verify = True
        for line in open(path):
            if not line.strip() or line.startswith('#'):
                continue # Skip blanks and comments
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue # Not a simple key/value, we can't parse it anyway
            key, value = parts
            md = cls.ruby_string_re.search(value)
            if md:
                value = md.group(2)
            elif key == 'ssl_verify_mode':
                log.debug('Found ssl_verify_mode: %r', value)
                ssl_verify = (value.strip() != ':verify_none')
                log.debug('ssl_verify = %s', ssl_verify)
            else:
                # Not a string, don't even try
                log.debug('Value for {0} does not look like a string: {1}'.format(key, value))
                continue
            def _ruby_value(match):
                expr = match.group(1).strip()
                if expr == 'current_dir':
                    return os.path.dirname(path)
                envmatch = cls.env_value_re.match(expr)
                if envmatch:
                    envmatch = envmatch.group(1).strip('"').strip("'")
                    return os.environ.get(envmatch) or ''
                log.debug('Unknown ruby expression in line "%s"', line)
                raise UnknownRubyExpression
            try:
                value = cls.ruby_value_re.sub(_ruby_value, value)
            except UnknownRubyExpression:
                continue
            if key == 'chef_server_url':
                log.debug('Found URL: %r', value)
                url = value
            elif key == 'node_name':
                log.debug('Found client name: %r', value)
                client_name = value
            elif key == 'client_key':
                log.debug('Found key path: %r', value)
                key_path = value
                if not os.path.isabs(key_path):
                    # Relative paths are relative to the config file
                    key_path = os.path.abspath(os.path.join(os.path.dirname(path), key_path))

        if not (url and client_name and key_path):
            # No URL, no chance this was valid, try running Ruby
            log.debug('No Chef server config found, trying Ruby parse')
            url = key_path = client_name = None
            proc = subprocess.Popen('ruby', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            script = config_ruby_script % path.replace('\\', '\\\\').replace("'", "\\'")
            out, err = proc.communicate(script)
            if proc.returncode == 0 and out.strip():
                data = json.loads(out)
                log.debug('Ruby parse succeeded with %r', data)
                url = data.get('chef_server_url')
                client_name = data.get('node_name')
                key_path = data.get('client_key')
            else:
                log.debug('Ruby parse failed with exit code %s: %s', proc.returncode, out.strip())
        if not url:
            # Still no URL, can't use this config
            log.debug('Still no Chef server URL found')
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
        return cls(url, key_path, client_name, ssl_verify=ssl_verify)

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
        return requests.api.request(method, url, headers=headers, data=data, verify=self.ssl_verify)

    def request(self, method, path, headers={}, data=None):
        auth_headers = sign_request(key=self.key, http_method=method,
            path=self.parsed_url.path+path.split('?', 1)[0], body=data,
            host=self.parsed_url.netloc, timestamp=datetime.datetime.utcnow(),
            user_id=self.client)
        request_headers = {}
        request_headers.update(self.headers)
        request_headers.update(dict((k.lower(), v) for k, v in six.iteritems(headers)))
        request_headers['x-chef-version'] = self.version
        request_headers.update(auth_headers)
        try:
            response = self._request(method, self.url + path, data, dict(
                (k.capitalize(), v) for k, v in six.iteritems(request_headers)))
        except requests.ConnectionError as e:
            raise ChefServerError(e.message)

        if not response.ok:
            raise ChefServerError.from_error(response.reason, code=response.status_code)

        return response

    def api_request(self, method, path, headers={}, data=None):
        headers = dict((k.lower(), v) for k, v in six.iteritems(headers))
        headers['accept'] = 'application/json'
        if data is not None:
            headers['content-type'] = 'application/json'
            data = json.dumps(data)
        response = self.request(method, path, headers, data)
        return response.json()

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
