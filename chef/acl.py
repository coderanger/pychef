import pkg_resources
from chef.api import ChefAPI
from chef.exceptions import ChefObjectTypeError
from chef.permissions import Permissions


class Acl(object):
    """
    Acl class provides access to the Acl in the Chef 12

        Acl(object_type, name, api, skip_load=False)

        - object_type - type of the Chef object. Can be one of the following value: "clients", "containers", "cookbooks",
            "data", "environments", "groups", "nodes", "roles"
        - name - name of the Chef object (e.g. node name)
        - api - object of the ChefAPI class, configured to work with Chef server
        - skip_load - is skip_load is False, new object will be initialized with current Acl settings of the specified
            object

        Example::

            from chef import ChefAPI
            from chef.acl import Acl

            api = ChefAPI('http://chef.com:4000', 'chef-developer.pem', 'chef-developer', '12.0.0')
            acl = Acl('nodes', 'i-022fcb0d', api)

        Each object of the Acl class contains the following properties:
            create, read, update, delete, grant
        each property represents corresponding access rights to the Chef object.
        each property contains the following fields (https://github.com/astryia/pychef/blob/acls/chef/permissions.py):
        - actors - list of the users, which have corresponding permissions
        - groups - list of the groups, which have corresponding permissions

        Example::

            print acl.update.groups
            >>> ['admins', 'clients']

        Each object of the class Acl contains the following methods:
        - reload() - reload current Acls from the Chef server
        - save() - save updated Acl object to the Chef server
        - is_supported() - return true if current Api version supports work with Acls

        Example::

            from chef import ChefAPI
            from chef.acl import Acl

            api = ChefAPI('http://chef.com:4000', 'chef-developer.pem', 'chef-developer', '12.0.0')
            acl = Acl('nodes', 'i-022fcb0d', api)
            print acl.update.groups
            >>> ['admins']
            acl.update.groups.append('clients')
            acl.save()
            acl.reload()
            print acl.update.groups
            >>> ['admins', 'clients']

        Each class which represents Chef object contains method get_acl() method

        Example::

            from chef import ChefAPI
            from chef.node import Node

            api = ChefAPI('http://chef.com:4000', 'chef-developer.pem', 'chef-developer', '12.0.0')
            node = Node('i-022fcb0d', api)
            acl = node.get_acl()
            print acl.read.groups
            >>> ['admins']
            acl.save()

        Note about versions
        Chef server with version < 12 doesn't have Acl endpoint, so, I've introduced method is_supported() for Acl class.
        This method check if api version is greater than 12.
        So you should pass valid Chef server version to the ChefAPI constructor

        Example::

            api = ChefAPI('http://chef.com:4000', 'chef-developer.pem', 'chef-developer', '12.0.0')
            acl = Acl('nodes', 'i-022fcb0d', api)
            print acl.is_supported()
            >>> True

            api = ChefAPI('http://chef.com:4000', 'chef-developer.pem', 'chef-developer', '11.2.0')
            acl = Acl('nodes', 'i-022fcb0d', api)
            print acl.is_supported()
            >>> False

        But if you pass string '12.0.0' when actual Chef server version is 11.2, you will receive an error when you try
        to build Acl object.
    """

    ace_types = ["create", "read", "update", "delete", "grant"]
    object_types = ["clients", "containers", "cookbooks", "data", "environments", "groups", "nodes", "roles"]

    """ ALC API available only in Chef server from version 12.0"""
    version = pkg_resources.parse_version("12.0.0")

    def __init__(self, object_type, name, api, skip_load=False):
        self._check_object_type(object_type)

        self.object_type = object_type
        self.name = name
        self.url = "/%s/%s/_acl/" % (object_type, name)
        self.api = api or ChefAPI.get_global()

        self.attributes_map = {}
        for t in self.ace_types:
            self.attributes_map[t] = Permissions()

        if (not skip_load) and self.is_supported():
            self.reload()

    @property
    def create(self):
        """ Gets Create permissions """
        return self.attributes_map["create"]

    @property
    def read(self):
        """ Gets Read permissions """
        return self.attributes_map["read"]

    @property
    def update(self):
        """ Gets Update permissions """
        return self.attributes_map["update"]

    @property
    def delete(self):
        """ Gets Delete permissions """
        return self.attributes_map["delete"]

    @property
    def grant(self):
        """ Gets Grant permissions """
        return self.attributes_map["grant"]

    def save(self):
        """ Save updated permissions objects to the Chef server """
        for t in self.ace_types:
            self.api.api_request('PUT', self.url + t, data={t: self[t]})

    def __getitem__(self, key):
        if key in self.attributes_map.keys():
            return self.attributes_map[key]
        else:
            return {}

    def reload(self):
        """ Load current permissions for the object """
        data = self.api.api_request('GET', self.url)
        for t in self.ace_types:
            self[t].actors = data[t]['actors']
            self[t].groups = data[t]['groups']

    def to_dict(self):
        d = {}
        for t in self.ace_types:
            d[t] = self[t].to_dict()

        return d

    def _check_object_type(self, object_type):
        if object_type not in self.object_types:
            raise ChefObjectTypeError('Object type %s is not allowed' % object_type)

    def is_supported(self):
        return self.api.version_parsed >= self.version
