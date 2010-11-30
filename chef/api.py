import copy
import datetime
import itertools
import logging
import os
import socket
import threading
import urllib2
import urlparse

from chef.auth import sign_request
from chef.rsa import Key
from chef.utils import json
from chef.utils.file import walk_backwards

api_stack = threading.local()
api_stack.value = []
log = logging.getLogger('chef.api')

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
    """A model for a Chef API server."""
    
    def __init__(self, url, key, client):
        self.url = url.rstrip('/')
        self.parsed_url = urlparse.urlparse(self.url)
        self.key = Key(key)
        self.client = client
        if not api_stack.value:
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
            if key == 'chef_server_url':
                url = value
            elif key == 'node_name':
                client_name = value
            elif key == 'client_key':
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
        if api_stack.value:
            return api_stack.value[-1]
    
    def set_default(self):
        """Make this the default API in the stack. Returns the old default if any."""
        old = None
        if api_stack.value:
            old = api_stack.value.pop(0)
        api_stack.value.insert(0, self)
        return old
    
    def __enter__(self):
        api_stack.value.append(self)
        return self
    
    def __exit__(self, type, value, traceback):
        del api_stack.value[-1]
    
    def request(self, method, path, headers={}, data=None):
        auth_headers = sign_request(key=self.key, http_method=method,
            path=self.parsed_url.path+path, body=data, host=self.parsed_url.netloc,
            timestamp=datetime.datetime.utcnow(), user_id=self.client)
        headers = copy.copy(headers)
        headers.update(auth_headers)
        request = ChefRequest(self.url+path, data, headers, method=method)
        try:
            response = urllib2.urlopen(request).read()
        except urllib2.HTTPError, e:
            print e.read()
            raise
        return response
    
    def api_request(self, method, path, headers={}, data=None):    
        headers = copy.copy(headers)
        headers['Accept'] = 'application/json'
        if data is not None:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data)
        response = self.request(method, path, headers, data)
        return json.loads(response)
    
    def __getitem__(self, path):
        return self.api_request('GET', path)

def autoconfigure(base_path=None):
    """Try to find a Knife or chef-client config file to load parameters from."""
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
    config_path = os.path.join(os.path.sep, 'etc', 'chef')
    api = ChefAPI.from_config_file(config_path)
    if api is not None:
        return api
